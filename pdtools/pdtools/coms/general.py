'''
Generic communication tasks. 
'''

from twisted.internet import defer
from twisted.internet import reactor

from pdtools.coms.client import RpcClient


###############################################################################
# Default Callbacks
###############################################################################

def defaultCallbacks(f):
    '''
    Wrap calls with default callbacks (print)
    '''

    def w(*args, **kwargs):
        return f(*args, **kwargs).addCallbacks(printSuccess, printFailure)

    return w


def printSuccess(r):
    print r


def printFailure(r):
    print 'Operation Failed!'
    print r


###############################################################################
# Generic Functionality
###############################################################################

@defer.inlineCallbacks
def logs(host, port):
    '''
    Connect to the named device and ask for logs.

    This will eventually be a server call, not a router call. 
    '''

    client = RpcClient(host, port, 'internal')

    response = yield client.log()

    # .log().addCallbacks(printSuccess, printFailure).addBoth(killReactor)
    # reactor.run()


@defaultCallbacks
@defer.inlineCallbacks
def echo(reactor, host, port):
    client = RpcClient(host, port, 'internal')
    res = yield client.echo('Hello!')
    defer.returnValue(res)
