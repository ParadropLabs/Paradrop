
# TODO add original licensing for this, don't remember where it came from

import re
from itertools import ifilter
from functools import wraps
from twisted.web.resource import Resource
from twisted.web.resource import NoResource
# DFW: I think this is old: from twisted.web.error import NoResource
from zope.interface.advice import addClassAdvisor
from twisted.web.server import NOT_DONE_YET

from paradrop.base.output import out
from paradrop.base.pdutils import str2json, explode
from paradrop.lib.misc import settings
from . import pdapi


class APIPackage():

    """
    This is a class that wrap up the input and return value of API
    The input arguments will be in the inputArgs as a dict
    Result is True means the API return success
    Result is False means the API return failure
    Result is None means the API return NOT_YET_DONE
    """

    def __init__(self, request):
        self.request = request
        # input values to the API
        self.inputArgs = {}
        # Return values from API
        self.result = True
        # On success
        self.returnVal = None
        # On failure
        self.errType = None
        self.errMsg = None
        self.countFailure = True
        # On NOT_YET_DONE

    def setSuccess(self, returnVal):
        self.result = True
        self.returnVal = returnVal

    def setFailure(self, errType, errMsg=None, countFailure=True):
        self.result = False
        self.errType = errType
        self.errMsg = errMsg
        self.countFailure = countFailure

    def setNotDoneYet(self):
        self.result = None

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
        def wrapper(theSelf, request, *args, **kwargs):
            tictoc = 0  # theSelf.perf.tic()
            ip = request.getClientIP()
            out.verbose('HTTP {} {} from {}'.format(request.method, request.path, ip))
            request.setHeader('Access-Control-Allow-Origin', settings.PDFCD_HEADER_VALUE)
            request.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT')

            apiPackage = APIPackage(request)
            # Extract required arguments
            if(requiredArgs or optionalArgs):
                body = str2json(request.content.read())
            if(requiredArgs):
                required = explode(body, *requiredArgs)
                for idx, arg in enumerate(requiredArgs):
                    # Check if required arg exist
                    if(required[idx] is None):
                        return theSelf.rest.failprocess(ip, request, (ip, theSelf.rest.clientFailures), "Malformed Body: %s", (tictoc, None), pdapi.ERR_BADPARAM)
                    # If exist put it into the apiPackage
                    apiPackage.inputArgs[arg] = required[idx]

            # Extract optional arguments
            if(optionalArgs):
                optional = explode(body, *optionalArgs)
                for idx, arg in enumerate(optionalArgs):
                    if(optional[idx]):
                        apiPackage.inputArgs[arg] = optional[idx]

            #######################################################################################
            # Make the real function call
            #######################################################################################
            func(theSelf, apiPackage, *args, **kwargs)

            # These assignments allow the SUCCESS and FAILURE code paths to
            # proceed without undefined variable exceptions, but I do not know
            # how they were originally intended to be assigned.
            failureKey = None
            failureDict = None
            devid = None

            # NOT_DONE_YET
            if(apiPackage.result is None):
                return NOT_DONE_YET
            # SUCCESS
            elif(apiPackage.result is True):
                theSelf.rest.postprocess(request, failureKey, failureDict, (tictoc, ip, devid))
                return apiPackage.returnVal
            # FAILURE
            else:
                errMsg = apiPackage.errMsg
                errType = apiPackage.errType
                if(apiPackage.countFailure):
                    # TODO: implement the failureKey and failureDict
                    return theSelf.rest.failprocess(ip, request, None, errMsg, (tictoc, devid), errType)
                else:
                    return theSelf.rest.failprocess(ip, request, None, errMsg, (tictoc, devid), errType)

        return wrapper
    return realDecorator
