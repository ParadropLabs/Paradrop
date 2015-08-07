'''
API exposed to pdtools and pdserver. 
'''

###############################################################################
# API
###############################################################################


from twisted.web import xmlrpc
from twisted.internet import defer, utils
from pdtools.coms.client import RpcClient

from pdtools.lib.output import out
from pdtools.lib import store, riffle, names


actual = None


def intermediate(logs):
    print 'Got some new logs!'
    actual(logs)

###############################################################################
# New Riffle Additions
###############################################################################


class ServerPerspective(riffle.RifflePerspective):

    @defer.inlineCallbacks
    def initialize(self):
        print 'SP initializing'
        yield 1

    @defer.inlineCallbacks
    def perspective_handshake(self):
        yield riffle.RifflePerspective.perspective_handshake(self)

    @defer.inlineCallbacks
    def perspective_subscribeLogs(self):
        '''
        Fetch all logs since the target time. Stream all new logs
        to the server as they come in. 
        '''

        out.addSubscriber(self.remote.newLogs)

        out.info('SEND SOMETHING')

        logs = yield out.getLogsSince(None)
        print 'Returning %s logs' % len(logs)

        print 'Server Perspective: ' + str(self)
        print 'SP Remote: ' + str(self.remote)

        defer.returnValue(logs)


class ToolsPerspective(riffle.RifflePerspective):
    pass


@defer.inlineCallbacks
def connectToServer(host):
    ''' Yet another temporary method '''
    avatar = yield riffle.portal.connect(host)

    # result = yield avatar.newLogs(['Hello from a client!'])

    # riffle.dumpRealms()

    defer.returnValue(avatar)


def checkStartRiffle():
    '''
    Temporary function. Do not start serving or connecting over riffle
    until we have our keys (which occurs during currently optional provisioning)
    '''

    if not riffle.portal.certCa:
        out.warn("Cannot start riffle server, no CA certificate found")
        return

    # Check to make sure we are not already listening!

    riffle.portal.addRealm(names.matchers[names.NameTypes.server], riffle.Realm(ServerPerspective))
    riffle.portal.addRealm(names.matchers[names.NameTypes.user], riffle.Realm(ToolsPerspective))

    # riffle.Riffle('localhost', port=8017).serve()

    # Open connection to the server
    from twisted.internet import reactor
    reactor.callLater(.1, connectToServer, 'localhost')


###############################################################################
# Old
###############################################################################

# @defaultCallbacks

@defer.inlineCallbacks
def echo(reactor, host):

    avatar = yield riffle.portal.connect(host)
    result = yield avatar.echo('Hello from a client!')
    riffle.dumpRealms()
    defer.returnValue(result)


@defer.inlineCallbacks
def api_echo(message):
    yield 1
    defer.returnValue(message)


@defer.inlineCallbacks
def api_log(lines=100):
    ''' Return the last number lines of the log. '''

    # if settings.LOG_PATH is None:
    #     raise Exception("Logging to file is not currently enabled.")

    # Fix this
    path = store.LOG_PATH + 'log'
    # path = os.path.dirname(os.getcwd()) + '/' + settings.LOG_NAME
    contents = yield utils.getProcessOutput('/usr/bin/tail', args=[path, '-n ' + str(lines), ])

    defer.returnValue(contents)


@defer.inlineCallbacks
def api_provision(pdid, publicKey, privateKey):
    '''
    Provision this router with an id and a set of keys. 

    This is a temporary call until the provisioning process is finalized.
    '''

    # Handshake with the server, ensuring the name is valid
    client = RpcClient('paradrop.io', 8015, '')

    store.store.saveConfig('pdid', pdid)
    store.store.saveKey(privateKey, 'private')
    store.store.saveKey(publicKey, 'public')

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
