'''
Communication with the server.

Top 10:
    House's Head/ Wilsons Heart
    Three Stories
    All In 
    Both sides now
'''

import getpass

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor

from pdtools.coms import general
from pdtools.coms.client import RpcClient
from pdtools.lib.store import store
from pdtools.lib import riffle, names, cxbr
from pdtools.lib.output import out
from pdtools.lib.exceptions import *

# HOST = "ws://127.0.0.s1:9080/ws"
HOST = "ws://paradrop.io:9080/ws"

###############################################################################
# Crossbar
###############################################################################


@general.failureCallbacks
@inlineCallbacks
def list(r):
    ''' Return the resources this user owns. '''

    pdid = store.getConfig('pdid')
    sess = yield cxbr.BaseSession.start(HOST, pdid)

    ret = yield sess.call('pd', 'list')

    store.saveConfig('chutes', ret['chutes'])
    store.saveConfig('routers', ret['routers'])
    store.saveConfig('instances', ret['instances'])

    printOwned()
    returnValue(None)


@general.failureCallbacks
@inlineCallbacks
def createRouter(r, name):
    ''' Create a new router. '''

    pdid = store.getConfig('pdid')
    sess = yield cxbr.BaseSession.start(HOST, pdid)

    name = pdid + '.' + name

    ret = yield sess.call('pd', 'provisionRouter', name)
    store.saveKey(ret['keys'], ret['_id'] + '.client.pem')

    ret = yield sess.call('pd', 'list')

    store.saveConfig('chutes', ret['chutes'])
    store.saveConfig('routers', ret['routers'])
    store.saveConfig('instances', ret['instances'])

    print 'New router successfully created'
    printOwned()


@general.failureCallbacks
@inlineCallbacks
def logs(r, target):
    '''
    Query the server for all logs that the given pdid has access to. Must be a fully qualified name.

    NOTE: in progress. For now, just pass the name of one of your routers.
    '''

    pdid = store.getConfig('pdid')
    sess = yield cxbr.BaseSession.start(HOST, pdid)

    # Note the lack of validation
    target = pdid + '.' + target
    print 'Asking for logs for ' + target

    # Rending method
    def printem(pdid, l):
        for x in l:
            print out.messageToString(x)

    oldLogs = yield sess.call('pd', 'getLogs', target, 0)

    printem(None, oldLogs)

    sub = yield sess.subscribe(printem, target, 'logs')


###############################################################################
# Authentication
###############################################################################

def authCallbacks(f):
    def w(*args, **kwargs):
        return f(*args, **kwargs).addCallbacks(authSuccess, general.printFailure)

    return w


def authSuccess(r):
    store.saveConfig('pdid', r['_id'])
    store.saveKey(r['keys'], 'client.pem')
    store.saveKey(r['ca'], 'ca.pem')

    print 'You have been successfully logged in.'


@authCallbacks
@inlineCallbacks
def login(reactor, host, port):
    name, password = None, None

    name = raw_input("Username: ")
    password = getpass.getpass()

    client = RpcClient(host, port, '')
    ret = yield client.login(name, password)
    returnValue(ret)


@authCallbacks
@inlineCallbacks
def register(reactor, host, port):
    name, email, pw, pw2 = raw_input("Username: "), raw_input("Email: "), getpass.getpass(), getpass.getpass(prompt='Reenter Password:')

    if pw != pw2:
        raise InvalidCredentials('Your passwords do not match.')

    client = RpcClient(host, port, '')
    ret = yield client.register(name, email, pw)

    print('By using this software you agree to our Privacy Policy as well as our Terms and Conditions.')
    print('  Privacy Policy:        https://paradrop.io/privacy-policy')
    print('  Terms and Conditions:  https://paradrop.io/terms-and-conditions')

    returnValue(ret)


###############################################################################
# Utils
###############################################################################

def printOwned():
    chutes = store.getConfig('chutes')
    routers = store.getConfig('routers')

    def pprint(d):
        print '\t' + d['_id']

    print 'routers'
    [pprint(x) for x in routers]

    print 'chutes'
    [pprint(x) for x in chutes]
