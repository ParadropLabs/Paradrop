import smokesignal
from twisted.web import xmlrpc
from twisted.internet import utils
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

from paradrop.lib import pdinstall
from pdtools.lib.output import out
from pdtools.lib import store, riffle, names, nexus, cxbr

HOST = 'localhost'
# HOST = 'paradrop.io'

###############################################################################
# Crossbar Additions
###############################################################################


class RouterSession(cxbr.BaseSession):

    @inlineCallbacks
    def onJoin(self, details):
        # TEMP: ping the server, let it know we just came up
        # yield self.call('pd', 'routerConnected', self._session_id)

        yield self.register(self.ping, 'ping')
        yield self.register(self.update, 'update')
        # yield self.register(self.logsFromTime, 'logsFromTime')

        # route output to the logs call
        smokesignal.on('logs', self.logs)

        yield cxbr.BaseSession.onJoin(self, details)

    @inlineCallbacks
    def logs(self, logs):
        ''' Called by the paradrop system when new logs come in '''

        # If ANYTHING throws an exception here you enter recursive hell,
        # since printing an exception will flood this method. No way out,
        # have to throw the logs away
        try:
            # Temp fix- these will eventually be batched as a list, but not yet
            logs = [logs]

            # Naive implementation: step 1- send logs to server
            yield self.call('pd', 'saveLogs', logs)

            # Step 2- broadcast our logs under our pdid
            yield self.publish(self.pdid, 'logs', logs)
        except:
            yield

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

    # @inlineCallbacks
    # def onLeave(self, details):
    #     print 'On Leave'
    # yield self.call('pd._disconnected', self.pdid)
    #     cxbr.BaseSession.onLeave(self, details)

    # def onDisconnect(self):
    #     out.info("Crossbar session detaching")

    # self.call('pd._disconnected', self.pdid)
    #     smokesignal.disconnect(self.logs)

    def ping(self, pdid):
        print 'Router ping'
        return 'Router ping receipt'

    def update(self, pdid, data):
        print("Sending command {} to pdinstall".format(data['command']))
        success = pdinstall.sendCommand(data['command'], data)

        # NOTE: If successful, this process will probably be going down soon.
        if success:
            return "Sent command to pdinstall"
        else:
            return "Sending command to pdinstall failed"


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
    # temp: check to make sure we're not already provisioned. Do not allow for
    # multiple provisioning. This is a little hacky-- better to move this into store
    if nexus.core.provisioned():
        raise ValueError("This device is already provisioned as " + nexus.core.info.pdid)

    # nexus.core.set('pdid', pdid)
    nexus.core.provision(pdid, None)

    nexus.core.saveKey(key, 'pub')
    nexus.core.saveKey(cert, 'ca')

    # Attempt to connect. WARNING- what happens if we're already connected?
    # Or if we timeout on the connection? The caller will never receive a response
    yield nexus.core.connect()

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
