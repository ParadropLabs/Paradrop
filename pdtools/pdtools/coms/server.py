'''
Communication with the server
'''

from pdtools.coms import general
from pdtools.coms.client import RpcClient
from pdtools.lib.store import store

from twisted.internet import defer
import getpass

###############################################################################
# Authentication Callbacks
###############################################################################


def authCallbacks(f):
    def w(*args, **kwargs):
        return f(*args, **kwargs).addCallbacks(authSuccess, general.printFailure)

    return w


def authSuccess(r):
    store.saveConfig('pdid', r['_id'])
    store.saveKey('public.pem', r['publicKey'])
    store.saveKey('private.pem', r['privateKey'])

    print 'You have been successfully logged in.'


@authCallbacks
@defer.inlineCallbacks
def login(reactor):
    name, password = None, None

    name = raw_input("Username: ")
    password = getpass.getpass()

    client = RpcClient(general.SERVER_HOST, general.SERVER_PORT, '')
    ret = yield client.login(name, password)
    defer.returnValue(ret)


@authCallbacks
@defer.inlineCallbacks
def register(reactor):
    name, email, password = raw_input("Username: "), raw_input("Email: "), getpass.getpass()

    client = RpcClient(general.SERVER_HOST, general.SERVER_PORT, '')
    ret = yield client.register(name, email, password)
    defer.returnValue(ret)


@general.failureCallbacks
@defer.inlineCallbacks
def ownership(reactor):
    ''' Get the list of owned resources from the server '''
    pdid = store.getConfig('pdid')
    client = RpcClient(general.SERVER_HOST, general.SERVER_PORT, '')
    ret = yield client.ownership(pdid)

    # Add these items to the store
    store.saveConfig('chutes', ret['chutes'])
    store.saveConfig('routers', ret['routers'])
    store.saveConfig('instances', ret['instances'])

    printOwned()

    defer.returnValue(ret)


@general.failureCallbacks
@defer.inlineCallbacks
def createRouter(reactor, name):
    ''' Get the list of owned resources from the server '''
    pdid = store.getConfig('pdid')

    client = RpcClient(general.SERVER_HOST, general.SERVER_PORT, '')
    ret = yield client.provisionRouter(pdid, name)

    print 'Router successfully created. Boot the router and run "provision," specifying the \
    address with port=14321'

    yield ownership(None)

    defer.returnValue(ret)


###############################################################################
# Utils
###############################################################################

# Show this individuallye (once for each type)
def printOwned():
    chutes = store.getConfig('chutes')
    routers = store.getConfig('routers')

    def pprint(d):
        print '\t' + d['_id']

    print 'routers'
    [pprint(x) for x in routers]

    print 'chutes'
    [pprint(x) for x in chutes]
