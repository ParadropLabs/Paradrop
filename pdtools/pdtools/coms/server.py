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
from pdtools.lib import nexus
from pdtools.lib.output import out
from pdtools.lib.exceptions import *


@inlineCallbacks
def list():
    ''' Return the resources this user owns. '''

    ret = yield nexus.core.session.call('pd', 'list')
    printOwned(ret)


@inlineCallbacks
def createRouter(name):
    ''' Create a new router. '''

    name = nexus.core.info.pdid + '.' + name

    ret = yield nexus.core.session.call('pd', 'provisionRouter', name)
    nexus.core.saveKey(ret['keys'], ret['_id'] + '.client.pem')

    ret = yield nexus.core.session.call('pd', 'list')
    print 'New router successfully created'
    printOwned(ret)


@inlineCallbacks
def logs(target):
    '''
    Query the server for all logs that the given pdid has access to. Must be a fully qualified name.

    NOTE: in progress. For now, just pass the name of one of your routers.
    TODO: check for bad router name. Happen on the server? Are we storing anything locally?
    '''

    # Note the lack of validation
    target = nexus.core.info.pdid + '.' + target
    print 'Asking for logs for ' + target

    # Rending method
    def printem(pdid, l):
        for x in l:
            print out.messageToString(x)

    oldLogs = yield nexus.core.session.call('pd', 'getLogs', target, 0)

    printem(None, oldLogs)

    sub = yield nexus.core.session.subscribe(printem, target, 'logs')

    # Never return, let the user stop with a keyboard interrupt
    # we could return if the router is offline, but user may want to wait
    # for it
    yield Deferred()


###############################################################################
# Authentication
###############################################################################

def authCallbacks(f):
    def w(*args, **kwargs):
        return f(*args, **kwargs).addCallbacks(authSuccess, general.printFailure)

    return w


def authSuccess(r):
    nexus.core.provision(r['_id'], None)

    nexus.core.saveKey(r['keys'], 'client.pem')
    nexus.core.saveKey(r['ca'], 'ca.pem')

    print 'You have been successfully logged in.'


@inlineCallbacks
def login(s):
    name, password = None, None
    name = raw_input("Username: ")
    password = getpass.getpass()
    # name, password = 'damouse', '12345678'

    ret = yield nexus.core.session.call('pd', 'login', name, password)
    authSuccess(ret)


@inlineCallbacks
def register(s):
    name, email, pw, pw2 = raw_input("Username: "), raw_input("Email: "), getpass.getpass(), getpass.getpass(prompt='Reenter Password:')

    if pw != pw2:
        raise InvalidCredentials('Your passwords do not match.')

    ret = yield nexus.core.session.call('pd', 'register', name, email, pw)
    authSuccess(ret)

    print('By using this software you agree to our Privacy Policy as well as our Terms and Conditions.')
    print('  Privacy Policy:        https://paradrop.io/privacy-policy')
    print('  Terms and Conditions:  https://paradrop.io/terms-and-conditions')


###############################################################################
# Utils
###############################################################################

def printOwned(owned):
    chutes = owned['chutes']
    routers = owned['routers']

    def pprint(d):
        print '\t' + d['_id']

    print 'routers'
    [pprint(x) for x in routers]

    print 'chutes'
    [pprint(x) for x in chutes]
