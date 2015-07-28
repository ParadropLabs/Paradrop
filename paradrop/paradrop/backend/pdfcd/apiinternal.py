'''
API exposed to pdtools and pdserver. 

These calls are not meant for user consumption and as such are SOAPy. This is a topic 
for debate. I believe this implementation is cleaner for developers without loss of 
functionality. 

These functions are inconsistent with the current api as defined, and because 
of this one or the other should be brought in line. The location of 
the API contents are not important (in terms of the route) since its easily moved, 
but consistency would be nice. 

I have done this in the interest of time and development speed. 
- Mickey

'''

###############################################################################
# API
###############################################################################


from twisted.web import xmlrpc
from twisted.internet import defer, utils
from pdtools.coms.client import RpcClient

from pdtools.lib.output import out
from pdtools.lib import store


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
    # ret = yield client.

    store.store.saveConfig('pdid', pdid)
    store.store.saveKey('private', privateKey)
    store.store.saveKey('public', publicKey)

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
