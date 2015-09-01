'''
Generic communication tasks. 

All remote calls are inline deferred callbacks. This allows them to be
easily chained together and fired asynchronously. 

Since calls are started with task.react, each method must take a reactor as its 
first parameter. 

Adding the defaultCallbacks decorator prints the result of the operation on 
success or failure. All failed calls return an exception which should be 
suitable for printing. 
'''

import re

from twisted.internet import defer
from autobahn.wamp import exception

from pdtools.coms.client import RpcClient
from pdtools.lib.output import out
from pdtools.lib import nexus


###############################################################################
# Boilerplate Callbacks
###############################################################################

def failureCallbacks(f):
    def w(*args, **kwargs):
        return f(*args, **kwargs).addErrback(printFailure)

    return w


def defaultCallbacks(f):
    ''' 
    Wrap the API call in default handlers which print results. Optional 
    params are used to turn off specific handlers
    '''
    def w(*args, **kwargs):
        return f(*args, **kwargs).addCallbacks(printSuccess, printFailure)

    return w


def printSuccess(r):
    if isinstance(r, list):
        for x in r:
            print x
    else:
        print r
    return r


def printFailure(r):

    # Autobahn cast exceptions
    if isinstance(r.value, exception.Error):
        print r.value.args[0]
        return None

    else:
        out.err('Unknown exception: ' + str(r))
        return r


###############################################################################
# Generic Functionality
###############################################################################

@defaultCallbacks
@defer.inlineCallbacks
def ping(sess):
    ret = yield nexus.core.session.call('pd', 'ping')
    print 'Ping result: ' + str(ret)
