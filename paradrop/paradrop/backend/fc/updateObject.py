
'''
updateObject module.

This holds onto the UpdateObject class.
It allows us to easily abstract away different update types and provide a uniform
way to interpret the results through a set of basic actionable functions.
'''
import time

from paradrop.backend import exc
from paradrop.backend.fc import chutestorage
from pdtools.lib.output import out
from paradrop.lib import settings
from paradrop.lib import chute

UPDATE_SPECIFIC_ARGS = ["pkg", "func"]


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
        # Pull in all the keys from the obj identified
        self.__dict__.update(obj)
        # Any module can add notes and warnings here
        self.responses = []
        # In case of a failure, the final message about failure goes here
        self.failure = None

        # Each update gets its own plan map
        self.plans = exc.plangraph.PlanMap(self.name)
        # Grab a reference to our storage system
        self.chuteStor = chutestorage.ChuteStorage()
        # Explicitly define a reference to the new data object
        self.new = chute.Chute(obj, strip=UPDATE_SPECIFIC_ARGS)
        # Grab the old version if it exists
        self.old = self.chuteStor.getChute(self.name)

        # Save a timestamp from when the update object was created.
        self.createdTime = time.time()

    def __repr__(self):
        return "<Update({}) :: {} - {} @ {}>".format(self.updateClass, self.name, self.updateType, self.tok)

    def __str__(self):
        return "<Update({}) :: {}>".format(self.updateClass, self.name)

    def saveState(self):
        """
            Function should be overwritten for each UpdateObject subtype
        """
        pass

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

        try:
            message = "Completed {} operation on chute {}: {}".format(
                self.updateType, self.new.name,
                "success" if kwargs['success'] else "failure")
            out.usage(message, chute=self.new.name, updateType=self.updateType,
                      createdTime=self.createdTime, startTime=self.startTime,
                      endTime=self.endTime, **kwargs)
        except Exception as e:
            out.exception(e, True)

        # Call the function we were provided
        self.func(self)

    def execute(self):
        """
        The function that actually walks through the main process required to create the chute.
        It follows the executeplan module through the paces of:
            1) Generate the plans for each exc module
            2) Prioritize the plans
            3) Execute the plans

        If at any point we fail then this function will directly take care of completing
        the update process with an error state and will close the API connection.
        """
        # Save a timestamp from when we started execution.
        self.startTime = time.time()

        # Generate the plans we need to setup the chute
        if(exc.executionplan.generatePlans(self)):
            out.warn('Failed to generate plans\n')
            self.complete(success=False, message=self.failure)
            return

        # Aggregate those plans
        exc.executionplan.aggregatePlans(self)

        # Execute on those plans
        if(exc.executionplan.executePlans(self)):
            # Getting here means we need to abort what we did
            res = exc.executionplan.abortPlans(self)

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

        # Now save the new state if we are all ok
        self.saveState()

        # Respond to the API server to let them know the result
        self.complete(success=True, message='Chute {} {} success'.format(
            self.name, self.updateType))


# This gives the new chute state if an update of a given type succeeds.
NEW_CHUTE_STATE = {
    'create': chute.STATE_RUNNING,
    'start': chute.STATE_RUNNING,
    'restart': chute.STATE_RUNNING,
    'delete': chute.STATE_STOPPED,
    'stop': chute.STATE_STOPPED
}


class UpdateChute(UpdateObject):

    """
    Updates specifically tailored to chute actions like create, delete, etc...
    """
    # List of all modules that need to be called during execution planning
    updateModuleList = [
        exc.name,
        exc.state,
        exc.struct,
        exc.resource,
        exc.traffic,
        exc.runtime
    ]

    def __init__(self, obj):
        updateType = obj.get('updateType', None)
        obj['state'] = NEW_CHUTE_STATE.get(updateType, chute.STATE_INVALID)

        super(UpdateChute, self).__init__(obj)

        # for start and restart updates we need to get the config info from the
        # old config without overwriting new update info
        if self.updateType == "start" or self.updateType == "restart":
            missingKeys = set(self.old.__dict__.keys()) - \
                          set(self.new.__dict__.keys())
            for k in missingKeys:
                setattr(self.new, k, getattr(self.old, k))

    def saveState(self):
        """
            For chutes specifically we need to change the chuteStor object to reflect
            the new state of the system after a chute update. Perform that update here.
        """
        if(self.updateType == "delete"):
            self.chuteStor.deleteChute(self.new)
        else:
            self.chuteStor.saveChute(self.new)


###################################################################################################
# Module functions and variables
###################################################################################################
UPDATE_CLASSES = {
    "CHUTE": UpdateChute
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
