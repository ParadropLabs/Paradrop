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

from paradrop.lib.utils.output import out, logPrefix


@defer.inlineCallbacks
def api_echo(message):
    yield 1
    defer.returnValue(message)


@defer.inlineCallbacks
def api_log(lines):
    ''' Return the last number lines of the log. '''
    contents = yield utils.getProcessOutput('/usr/bin/tail', args=['/home/damouse/Documents/python/scratch/popen.txt'])
    defer.returnValue(contents)

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
    out.info("-- Failed API call (TODO: categorize errors)")

    raise xmlrpc.Fault(123, failure.getErrorMessage())


def apiWrapper(target):
    ''' Add a final line of error and success callbacks before going onto the wire'''

    def outside(*args):
        return target(*args).addErrback(castFailure).addCallback(castSuccess)

    return outside


def castSuccess(res):
    out.info("-- Completed API call (TODO: add details)")

    # screen out Objectids on mongo returns. The remote objects have no
    # need for them, and they confuse xmlrpc
    if isinstance(res, dict):
        res.pop('_id', None)

    return res
