'''
This holds onto the UpdateObject class.
It allows us to easily abstract away different update types and provide a uniform
way to interpret the results through a set of basic actionable functions.
'''
from __future__ import print_function
import time
from twisted.internet import defer, reactor
from twisted.python.failure import Failure

from paradrop.base import nexus, settings
from paradrop.base.output import out
from paradrop.core import plan
from paradrop.core.chute.builder import build_chute, rebuild_chute
from paradrop.core.chute.chute import Chute
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.agent.http import PDServerRequest

from paradrop.core.plan import executionplan
from paradrop.core.plan import hostconfig
from paradrop.core.plan import name
from paradrop.core.plan import resource
from paradrop.core.plan import router
from paradrop.core.plan import runtime
from paradrop.core.plan import snap
from paradrop.core.plan import state
from paradrop.core.plan import struct
from paradrop.core.plan import traffic

# Examples of update objects, first from local installation, second from cloud
# update.
#
# {'web': {'port': 8080}, 'workdir': '/tmp/tmpo67yf7', 'name': 'go-hello-world', 'deferred': <Deferred at 0x7f46dc5fae18>, 'updateType': 'create', 'state': 'running', 'tok': 1524765733, 'updateClass': 'CHUTE', 'version': 'x1524765733', 'change_id': 2}
#
# {u'web': {u'port': u'8080'}, u'name': u'go-hello-world', 'deferred': <Deferred at 0x7f46dc5adfc8>, 'updateType': u'update', 'state': 'running', 'tok': 1524765792, 'updateClass': u'CHUTE', u'version': 1, 'external': {'chute_id': u'5ae20aa29ca0e4049ca2fff3', 'update_id': u'5ae2145f9ca0e4049ca3017d', 'version_id': u'5ae20ab59ca0e4049ca2fff8'}, 'change_id': 3, u'download': {u'url': u'https://github.com/ParadropLabs/go-hello-world', u'checkout': u'master'}}


class UpdateObject(object):

    """
    The base UpdateObject class, covers a few basic methods but otherwise all the intelligence
    exists in the inherited classes.

    All update information passed by the API server is contained as variables of this class
    such as update.updateType, update.updateClass, etc...

    By default, the following variables should be utilized:
        responses : an array of messages any module can choose to append warnings or errors to

        failure   : the module that chose to fail this update can set a string message to return
                  : to the user in the failure variable. It should be very clear as to why the
                  : failure occurred, but if the user wants more information they may find it
                  : in the responses variable which may contain debug information, etc...
    """
    updateModuleList = []

    def __init__(self, obj):
        self.change_id = None
        self.pkg = None

        # Pull in all the keys from the obj identified
        self.__dict__.update(obj)
        # Any module can add notes and warnings here
        self.responses = []
        # In case of a failure, the final message about failure goes here
        self.failure = None

        # Each update gets its own plan map
        self.plans = plan.plangraph.PlanMap(self.name)
        # Grab a reference to our storage system
        self.chuteStor = ChuteStorage()

        # Build new Chute object.
        self.new = build_chute(obj)

        # Grab the old version if it exists
        self.old = self.chuteStor.getChute(self.name)

        # Save a timestamp from when the update object was created.
        self.createdTime = time.time()

        # Set to True if this update is delegated to an external program (e.g.
        # pdinstall).  In that case, the external program will be responsible
        # for reporting on the completion status of the update.
        self.delegated = False

        # Store progress messages so that they can be retrieved by API.
        self.messages = []
        self.message_observers = []
        self.completed = False

        # Cache for passing intermediate values between plan functions.
        # Previously, this was all done in the chute object, but the
        # functionality extends to other operations such as a node
        # configuration change.
        self.cache = {}

        # Set by the execute function on the first call and used to detect
        # whether its new or has been resumed.
        self.execute_called = False

    def __repr__(self):
        return "<Update({}) :: {} - {} @ {}>".format(self.updateClass, self.name, self.updateType, self.tok)

    def __str__(self):
        return "<Update({}) :: {}>".format(self.updateClass, self.name)

    def started(self):
        """
        This function should be called when the updated object is dequeued and
        execution is about to begin.

        Sends a notification to the pdserver if this is a tracked update.
        """
        # TODO Look into this.
        # This might happen during router initialization.  If nexus.core is
        # None, we do not know the router's identity, so we cannot publish any
        # messages.
        if nexus.core is None:
            return

        # The external field is set for updates from pdserver but not for
        # locally-initiated (sideloaded) updates.
        if not self.execute_called and hasattr(self, 'external'):
            update_id = self.external['update_id']
            request = PDServerRequest('/api/routers/{router_id}/updates/' + str(update_id))
            request.patch({'op': 'replace', 'path': '/started', 'value': True})

    def progress(self, message):
        if self.pkg is not None:
            self.pkg.request.write(message + '\n')

        # TODO Look into this.
        # This might happen during router initialization.  If nexus.core is
        # None, we do not know the router's identity, so we cannot publish any
        # messages.
        if nexus.core is None:
            return

        data = {
            'time': time.time(),
            'message': message
        }

        def handleError(error):
            print("Error sending message: {}".format(error.getErrorMessage()))

        # The external field is set for updates from pdserver but not for
        # locally-initiated (sideloaded) updates.
        update_id = None
        if hasattr(self, 'external'):
            update_id = self.external['update_id']
            request = PDServerRequest('/api/routers/{}/updates/{}/messages'
                    .format(nexus.core.info.pdid, update_id))
            d = request.post(**data)
            d.addErrback(handleError)

        session = getattr(nexus.core, 'session', None)
        if session is not None:
            data['update_id'] = update_id

            # Catch the occasional Exception due to connectivity failure.  We
            # don't want to fail a chute installation just because we had problems
            # sending the log messages.
            try:
                session.publish(session.uriPrefix + 'updateProgress', data)
            except Exception as error:
                out.warn("Publish failed: {} {}".format(error.__class__, error))

        # Send messages to internal consumers (e.g. open websocket connections)
        self.messages.append(data)
        for observer in self.message_observers:
            observer.on_message(data)

    def complete(self, **kwargs):
        """
            Signal to the API server that any action we need to perform is
            complete and the API server can finish its connection with the
            client that initiated the API request.
        """
        # Save a timestamp from when we finished execution.
        self.endTime = time.time()

        if(settings.DEBUG_MODE):
            kwargs['responses'] = self.responses

        # Set our results
        self.result = kwargs

        d = None
        if hasattr(self, 'deferred'):
            d = self.deferred
            self.deferred = None

        try:
            message = "Completed {} operation on chute {}: {}".format(
                self.updateType, self.new.name,
                "success" if kwargs['success'] else "failure")
            out.usage(message, chute=self.new.name, updateType=self.updateType,
                      createdTime=self.createdTime, startTime=self.startTime,
                      endTime=self.endTime, **kwargs)
        except Exception as e:
            out.exception(e, True)
            if d:
                reactor.callFromThread(d.errback, Failure(e))

        # Last message to send to observers.
        msg = {
            'time': self.endTime,
            'message': message
        }
        self.messages.append(msg)

        # Mark the update as complete and notify any observers. Observers
        # should call remove_message_observer in their on_complete handler.
        self.completed = True
        for observer in self.message_observers:
            observer.on_message(msg)
            observer.on_complete()

        if 'message' in kwargs:
            self.progress(kwargs['message'])

        if d:
            reactor.callFromThread(d.callback, self)

    def execute(self):
        """
        The function that actually walks through the main process required to create the chute.
        It follows the executeplan module through the paces of:
            1) Generate the plans for each plan module
            2) Prioritize the plans
            3) Execute the plans

        If at any point we fail then this function will directly take care of completing
        the update process with an error state and will close the API connection.
        """
        if not self.execute_called:
            # Save a timestamp from when we started execution.
            self.startTime = time.time()

            # Generate the plans we need to setup the chute
            if(executionplan.generatePlans(self)):
                out.warn('Failed to generate plans\n')
                self.complete(success=False, message=self.failure)
                return

            # Aggregate those plans
            executionplan.aggregatePlans(self)

            self.execute_called = True

        # Execute on those plans
        exec_result = executionplan.executePlans(self)
        if isinstance(exec_result, defer.Deferred):
            return exec_result
        elif exec_result is True:
            # Getting here means we need to abort what we did
            res = executionplan.abortPlans(self)

            # Did aborting also fail? This is bad!
            if(res):
                ###################################################################################
                # Getting here means the abort system thinks it wasn't able to get the system
                # back into the state it was in prior to this update.
                ###################################################################################
                out.err('TODO: What do we do when we fail during abort?\n')
                pass

            # Report the failure back to the user
            self.complete(success=False, message=self.failure)
            return

        # Respond to the API server to let them know the result
        self.complete(success=True, message='Chute {} {} success'.format(
            self.name, self.updateType))

    def add_message_observer(self, observer):
        for msg in self.messages:
            observer.on_message(msg)

        self.message_observers.append(observer)

        # If the update is already complete, send the complete event. Other
        # observers would have already received this.
        if self.completed:
            observer.on_complete()

    def remove_message_observer(self, observer):
        self.message_observers.remove(observer)

    def has_chute_build(self):
        """
        Check whether this update involves building a chute.
        """
        return False

    def cache_get(self, key, default=None):
        """
        Get a value from the cache or the default value if it does not exist.
        """
        return self.cache.get(key, default)

    def cache_set(self, key, value):
        """
        Set a value in the cache.
        """
        self.cache[key] = value


# This gives the new chute state if an update of a given type succeeds.
NEW_CHUTE_STATE = {
    'create': Chute.STATE_RUNNING,
    'update': Chute.STATE_RUNNING,
    'start': Chute.STATE_RUNNING,
    'restart': Chute.STATE_RUNNING,
    'delete': Chute.STATE_STOPPED,
    'stop': Chute.STATE_STOPPED
}


class UpdateChute(UpdateObject):
    """
    Updates specifically tailored to chute actions like create, delete, etc...
    """

    # List of all modules that need to be called during execution planning
    updateModuleList = [
        name,
        state,
        struct,
        resource,
        traffic,
        runtime
    ]

    def __init__(self, obj, reuse_existing=False):
        """
        Create an update object that affects a chute.

        Args:
            obj (dict): update specification.
            reuse_existing (bool): use the existing Chute object from storage, e.g.
                when restarting a chute without changes.
        """
        updateType = obj.get('updateType', None)

        # TODO: Remove this if unused. It is not the update that has a running
        # state but rather the chute.
        obj['state'] = NEW_CHUTE_STATE.get(updateType, Chute.STATE_INVALID)

        super(UpdateChute, self).__init__(obj)

        # If going from one version of a chute to another, try to fill in
        # any missing values in the new chute using the old chute.
        if reuse_existing:
            self.new = self.old
        elif self.old is not None:
            old_spec = self.old.create_specification()
            self.new = rebuild_chute(old_spec, obj)

        self.new.state = NEW_CHUTE_STATE.get(updateType, Chute.STATE_INVALID)

    def has_chute_build(self):
        """
        Check whether this update involves building a chute.
        """
        return self.updateType in ["create", "update"]


class UpdateRouter(UpdateObject):
    """
    Updates specifically tailored to router configuration.
    """
    # List of all modules that need to be called during execution planning
    #
    # All of the modules listed in UpdateChute perform an extensive series of
    # steps that are largely irrelevant for host config updates.  Therefore, we
    # use a different module here.
    updateModuleList = [
        hostconfig,
        router
    ]


class UpdateSnap(UpdateObject):
    """
    Updates specifically tailored to installing snaps.
    """
    # List of all modules that need to be called during execution planning
    #
    # All of the modules listed in UpdateChute perform an extensive series of
    # steps that are largely irrelevant for host config updates.  Therefore, we
    # use a different module here.
    updateModuleList = [
        snap
    ]


###################################################################################################
# Module functions and variables
###################################################################################################
UPDATE_CLASSES = {
    "CHUTE": UpdateChute,
    "ROUTER": UpdateRouter,
    "SNAP": UpdateSnap
}


def parse(obj):
    """
    Determines the update type and returns the proper class.
    """
    uclass = obj.get('updateClass', None)
    cls = UPDATE_CLASSES.get(uclass, None)

    if(cls is None):
        raise Exception('BadUpdateType', 'updateClass is invalid, must be one of: %s' % ", ".join(UPDATE_CLASSES))
    return cls(obj)
