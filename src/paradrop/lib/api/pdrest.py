
# TODO add original licensing for this, don't remember where it came from

import re
from itertools import ifilter
from functools import wraps
from twisted.web.resource import Resource
from twisted.web.resource import NoResource
#DFW: I think this is old: from twisted.web.error import NoResource
from zope.interface.advice import addClassAdvisor

def method_factory_factory(method):
    def factory(regex):
        _f = {}
        def decorator(f):
            _f[f.__name__] = f
            return f
        def advisor(cls):
            def wrapped(f):
                def __init__(self, *args, **kwargs):
                    f(self, *args, **kwargs)
                    for func_name in _f:
                        orig = _f[func_name]
                        func = getattr(self, func_name)
                    if func.im_func==orig:
                        self.register(method, regex, func)
                return __init__
            cls.__init__ = wrapped(cls.__init__)
            return cls
        addClassAdvisor(advisor)
        return decorator
    return factory

ALL    = method_factory_factory('ALL')
GET    = method_factory_factory('GET')
POST   = method_factory_factory('POST')
PUT    = method_factory_factory('PUT')
DELETE = method_factory_factory('DELETE')

class _FakeResource(Resource):
    _result = ''
    isLeaf = True
    def __init__(self, result):
        Resource.__init__(self)
        self._result = result
    def render(self, request):
        return self._result


def maybeResource(f):
    @wraps(f)
    def inner(*args, **kwargs):
        result = f(*args, **kwargs)
        if not isinstance(result, Resource):
            result = _FakeResource(result)
        return result
    return inner


class APIResource(Resource):

    _registry = None

    def __init__(self, *args, **kwargs):
        Resource.__init__(self, *args, **kwargs)
        self._registry = []

    def _get_callback(self, request):
        filterf = lambda t:t[0] in (request.method, 'ALL')
        for m, r, cb in ifilter(filterf, self._registry):
            result = r.search(request.path)
            if result:
                return cb, result.groupdict()
        return None, None

    def register(self, method, regex, callback):
        self._registry.append((method, re.compile(regex), callback))

    def unregister(self, method=None, regex=None, callback=None):
        if regex is not None: regex = re.compile(regex)
        for m, r, cb in self._registry[:]:
            if not method or (method and m==method):
                if not regex or (regex and r==regex):
                    if not callback or (callback and cb==callback):
                        self._registry.remove((m, r, cb))

    def getChild(self, name, request):
        r = self.children.get(name, None)
        if r is None:
            # Go into the thing
            callback, args = self._get_callback(request)
            if callback is None:
                return NoResource()
            else:
                return maybeResource(callback)(request, **args)
        else:
            return r

def APIDecorator(admin=False, permission=None, requiredArgs=[], optionalArgs=[]):
    """
        The decorator for the API functions to make the API functions focus on their job.
        This decorator do the following things:
            * Set HTTP header
            * Get some common values like ip, tictoc
            * Do the preprocess
            * Extract arguments from HTTP body and put them into APIPackage
            * Get devid if token is shown and put devid into APIPackage
            * Check admin authorization if devid is shown and admin argument is set to be true
            * Do the failprocess if fails. Do the postProcess if success
        This decorator will pass an APIPackage to an API function and the API function is supposed to put return value into the API package
        Arguments:
            * admin: if the function needs admin authority to call
            * requiredArgs: the required arguments for this API, this wrapper will parse the required args from HTTP body and check if they exist in the body.
            * optionalArgs: the optional arguments for this API, the args will be parsed from HTTP body
            * permission: choose from None, "AP Owner", "Chute Owner"
        TODO: 
            1.Permission
                * multiple permission/multiple level of permission??
                * More permissions: such as Vnet Owner, Group Owner
    """
    def realDecorator(func):
        def wrapper(theSelf, request, **args):
            tictoc = theSelf.perf.tic()
            ip = getIP(request)
            out.verbose('-- %s HTTP request from IP %s\n' % (logPrefix(), ip))
            request.setHeader('Access-Control-Allow-Origin', settings.DBAPI_HEADER_VALUE)

            
            apiPackage = APIPackage()
            # Extract required arguments
            if(requiredArgs or optionalArgs):
                body = str2json(request.content.read())
            if(requiredArgs):
                required = pdutils.explode(body, *requiredArgs)
                for idx, arg in enumerate(requiredArgs):
                    # Check if required arg exist
                    if(required[idx] is None):
                        return theSelf.rest.failprocess(ip, request, (ip, theSelf.rest.clientFailures), "Malformed Body: %s", (tictoc, None), pdapi.ERR_BADPARAM)
                    # If exist put it into the apiPackage
                    apiPackage.inputArgs[arg] = required[idx]
            
            # Extract optional arguments
            if(optionalArgs):
                optional = pdutils.explode(body, *optionalArgs)
                for idx, arg in enumerate(optionalArgs):
                    if(optional[idx]):
                        apiPackage.inputArgs[arg] = optional[idx]

            # Determine which failureDict to use based on the function name
            # Kaichen: Here we have an assumption that the signin function in Auth module is the only 
            #          function that use uname as key and use the signinFailures as the failure dict.
            #          Other APIs use ip as key and use clientFailure as the failure dict.
            if(func.__name__ == "POST_signin"):
                failureKey = apiPackage.inputArgs.get("username")
                failureDict = theSelf.signinFailures
            else:
                failureKey = ip
                failureDict = theSelf.rest.clientFailures

            token = apiPackage.inputArgs.get("sessionToken", None)
            # Do the preprocess
            res = theSelf.rest.preprocess(request, (ip, token, failureKey, failureDict), tictoc)
            if(res):
                return res

            # Get the devid and put it into apiPackage if token exist            
            devid = None

            if(token):
                devid = theSelf.rest.userCache.getDevidFromToken(token)
                if(devid is None):
                    return theSelf.rest.failprocess(ip, request, (failureKey, failureDict), 'Bad Token: %s', (tictoc, None), pdapi.ERR_BADAUTH)
                apiPackage.inputArgs["devid"] = devid

            # Find the real apid if the apid is an ap name
            apid = apiPackage.inputArgs.get("apid", None)
            if(apid and not pdutils.isGuid(apid)):
                apid = pddb.getApidByName(theSelf.dbh, apid)
                if(apid is None):
                    out.err("!! %s Bad apid: %s\n" % (logPrefix(ip), apid))
                    return theSelf.rest.failprocess(ip, request, (ip, theSelf.rest.clientFailures), 'Bad apid: %s', (tictoc, None),pdapi.getResponse(pdapi.ERR_BADAUTH))
                else:
                    apiPackage.inputArgs['apid'] = apid

            # Check admin 
            if(admin):
                user = self.rest.userCache.getUserFromToken(token)
                if(user['admin'] != 1):
                    return self.rest.failprocess(ip, request, (failureKey, failureDict), "Unauthorized: %s", (tictoc, devid), pdapi.ERR_BADAUTH)

            # Bypass permission check for the testingAdmin user
            if(devid != settings.DBAPI_ADMIN_DEVID):            
                # Check permission
                if(permission):
                    chuteid = apiPackage.inputArgs.get("chuteid", None)
                    apid = apiPackage.inputArgs.get("apid", None)
                    # AP owner
                    if(permission == "AP Owner" and not pddb.checkAPDevPermissions(theSelf.dbh, devid, apid)):
                        out.err("!! %s Developer %s doesn't permission to AP: %s\n" % (logPrefix(ip), devid, apid))
                        return theSelf.rest.failprocess(ip, request, (ip, theSelf.rest.clientFailures), "Developer has no permission to AP:%s" % apid + " %s", (tictoc, None), pdapi.ERR_BADAUTH)
                    # chute owner
                    elif(permission == "Chute Owner" and not pddb.isDevChuteOwner(theSelf.dbh, devid, chuteid)):
                        out.err("!! %s Developer %s has no permission on chute %s\n" % (logPrefix(ip), devid, chuteid))
                        return theSelf.rest.failprocess(ip, request, (ip, theSelf.rest.clientFailures), "Developer has no permission on chute" + chuteid+  ": %s", (tictoc, devid), pdapi.ERR_BADAUTH)
                    elif(permission != "Chute Owner" and permission != "AP Owner"):
                        out.err("!! Bad usage of api decorator, invalid permission\n")

            # Call the real API function
            apiPackage.inputArgs['request'] = request
            func(theSelf, apiPackage, **args)
            # NOT_DONE_YET
            if(apiPackage.result is None):
                return NOT_DONE_YET
            # SUCCESS
            elif(apiPackage.result):
                theSelf.rest.postprocess(request, failureKey, failureDict, (tictoc, ip, devid))
                return apiPackage.returnVal
            # FAILURE
            else:
                errMsg = apiPackage.errMsg
                errType = apiPackage.errType
                if(apiPackage.countFailure):
                    return theSelf.rest.failprocess(ip, request, (failureKey, failureDict), errMsg, (tictoc, devid), errType)
                else:
                    return theSelf.rest.failprocess(ip, request, None, errMsg, (tictoc, devid), errType)
                
        return wrapper
    return realDecorator



