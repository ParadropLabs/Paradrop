import smokesignal
from twisted.web import xmlrpc
from twisted.internet import utils
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

from pdtools.lib.output import out
from pdtools.lib import store, riffle, names, nexus, cxbr

HOST = 'localhost'
# HOST = 'paradrop.io'

###############################################################################
# Crossbar Additions
###############################################################################


class CrossApi(cxbr.BaseSession):

    def __init__(self, config=None):
        cxbr.BaseSession.__init__(self, config=config)
        self.pdid = config.extra

    @inlineCallbacks
    def onJoin(self, details):
        cxbr.BaseSession.onJoin(self, details)

        out.info("Crossbar session attached")

        # TEMP: ping the server, let it know we just came up
        self.call('pd._connected', self.pdid, self._session_id)

        print 'Registering under ' + self.pdid
        yield self.register(self.ping, u'' + self.pdid + '.ping')
        yield self.register(self.logsFromTime, u'' + self.pdid + '.logsFromTime')

        # Note: although all logs can simply be published as generated, I'm
        # sticking to the old model of subscribing to the logs seperately
        # from their crossbar publish. There are a host of situations where
        # we may not want to push all the logs to the router constantly--
        # direct crossbar publishing of logs can therefor only work if the
        # local router is smart enough not to push when no remote subscriptions are active

        # route output to the logs call
        smokesignal.on('logs', self.logs)

    def logs(self, logs):
        ''' Called by the paradrop system when new logs come in '''
        logId = u'' + self.pdid + '.logs'
        self.publish(logId, self.pdid, logs)

    def logsFromTime(self, start):
        '''
        Loads logs that have timestamps after the given time. 

        :param start: seconds since epoch from which to start returning logs
        :type start: int.
        :returns: list of logs
        '''

        return out.getLogsSince(start, purge=False)

    # Does not allow the shutdown call to go out before the system goes down
    # @inlineCallbacks
    # def onClose(self, a):
    #     print 'Asked to close!'
    #     yield self.call('pd._disconnected', self.pdid)

    @inlineCallbacks
    def onLeave(self, details):
        print 'On Leave'
        yield self.call('pd._disconnected', self.pdid)
        cxbr.BaseSession.onLeave(self, details)

    def onDisconnect(self):
        out.info("Crossbar session detaching")

        # self.call('pd._disconnected', self.pdid)
        smokesignal.disconnect(self.logs)

    def ping(self):
        print 'Router ping'
        return


###############################################################################
# New Riffle Additions
###############################################################################

class ServerPerspective(riffle.RifflePerspective):

    def initialize(self):
        # The function target that subscribes to output events
        self.subscribed = None

    def destroy(self):
        # Remove the log subscriber when the connection goes down.
        if self.subscribed is not None:
            out.removeSubscriber(self.subscribed)

    @inlineCallbacks
    def perspective_subscribeLogs(self, target):
        '''
        Fetch all logs since the target time. Stream all new logs
        to the server as they come in. 
        '''

        # Adds the target function (newLogs) to out's streaming subscription set
        # Do not do this without the user's consent
        out.addSubscriber(self.remote.newLogs)
        self.subscribed = self.remote.newLogs

        logs = yield out.getLogsSince(target)

        returnValue(logs)


class ToolsPerspective(riffle.RifflePerspective):
    pass


def pollServer(host):
    '''
    Poll the server for a connection.
    '''

    def success(a):
        print 'Connected to server!'

    riffle.portal.pollConnect(success, host=host)


def checkStartRiffle():
    '''
    Temporary function. Do not start serving or connecting over riffle
    until we have our keys (which occurs during currently optional provisioning)
    '''

    if not riffle.portal.certCa:
        out.warn("Cannot start riffle server, no CA certificate found")
        return

    out.info('Received certs, opening riffle portal')

    # Check to make sure we are not already listening
    # as of this writing we are not checking for previously-provisioned state)

    # Open connection to the server
    from twisted.internet import reactor
    reactor.callLater(.1, riffle.portal.connect, HOST)


###############################################################################
# Old
###############################################################################

@inlineCallbacks
def api_provision(pdid, key, cert):
    '''
    Provision this router with an id and a set of keys. 

    This is a temporary call until the provisioning process is finalized.
    '''

    # SO TEMP IT HURTS:
    # yield
    # ret = {'root': nexus.core.rootPath, 'logs': nexus.core.logPath}
    # returnValue(ret)

    # temp: check to make sure we're not already provisioned. Do not allow for
    # multiple provisioning. This is a little hacky-- better to move this into store
    if riffle.portal.certCa:
        raise ValueError("This device is already provisioned as " + nexus.core.get('pdid'))

    nexus.core.set('pdid', pdid)
    nexus.core.saveKey(key, 'pub')
    nexus.core.saveKey(cert, 'ca')

    riffle.portal.keyPrivate = key
    riffle.portal.certCa = cert

    # If we are being provisioned for the first time, start riffle services
    yield checkStartRiffle()

    nexus.core.connect()

    # Return success to the user
    returnValue('Done!')

###############################################################################
# Temporary-- this needs a home, haven't decided where yet.
###############################################################################


class Base(xmlrpc.XMLRPC):

    def __init__(self, module, **kwargs):
        xmlrpc.XMLRPC.__init__(self, kwargs)

        # build a dict of exposed api methods
        self.apiFunctions = {k.replace('api_', ''): apiWrapper(getattr(module, k)) for k in dir(module) if 'api_' in k}

    def lookupProcedure(self, procedurePath):
        try:
            return self.apiFunctions[procedurePath]
        except KeyError:
            raise xmlrpc.NoSuchFunction(self.NOT_FOUND, "procedure %s not found" % procedurePath)


def castFailure(failure):
    ''' Converts an exception (or general failure) into an xmlrpc fault for transmission. '''
    out.info("Failed API call (TODO: categorize errors)")

    raise xmlrpc.Fault(123, failure.getErrorMessage())


def apiWrapper(target):
    ''' Add a final line of error and success callbacks before going onto the wire'''

    def outside(*args):
        return target(*args).addErrback(castFailure).addCallback(castSuccess)

    return outside


def castSuccess(res):
    out.info("Completed API call (TODO: add details)")

    # screen out Objectids on mongo returns. The remote objects have no
    # need for them, and they confuse xmlrpc
    if isinstance(res, dict):
        res.pop('_id', None)

    return res
