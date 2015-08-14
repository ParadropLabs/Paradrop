from twisted.web import xmlrpc
from twisted.internet import defer, utils
from pdtools.coms.client import RpcClient

from pdtools.lib.output import out
from pdtools.lib import store, riffle, names

from pdtools.lib import nexus

HOST = 'localhost'
# HOST = 'paradrop.io'

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

    @defer.inlineCallbacks
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

        defer.returnValue(logs)


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

@defer.inlineCallbacks
def api_provision(pdid, key, cert):
    '''
    Provision this router with an id and a set of keys. 

    This is a temporary call until the provisioning process is finalized.
    '''

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
    checkStartRiffle()

    yield 1
    defer.returnValue(None)

    # Return success to the user

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
