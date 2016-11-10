####################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

'''
pdfcd.server.
Contains the classes required to establish a RESTful API server using Twisted.
'''
from twisted.web.server import Site
from twisted.internet import reactor

from pdtools.lib.output import out
from pdtools.lib import names

from pdtools.lib.pdutils import timeflt, str2json, json2str
from paradrop.lib.api import pdapi
from txrestapi.resource import APIResource
from txrestapi.methods import GET, POST, PUT, ALL
from paradrop.lib import settings
from paradrop.lib.container import dockerapi
from paradrop.lib.procmon import ProcessMonitor
from paradrop.backend.fc import configurer


# Import local refs to pdfcd utilities
from . import apibridge
from . import apiutils
from . import apichute
from . import apiconfig
from . import apistatus

# temp
from paradrop.backend.pdfcd import apiinternal


class AccessInfo(object):

    """
    Track accesses to PDAPI server.

    TODO: Implement this class if needed.
    """

    def __init__(self, ip, headers, time):
        self.attempts = 1

    def update(self, ip, headers, time):
        self.attempts += 1


class ParadropAPIServer(APIResource):

    """
    The main API server module.

    This sets up all of the submodules which should contain different types of RESTful API calls.
    """

    # Whitelist of addresses
    # NOTE This functionality does not seem to be fully implemented.
    WHITELIST_IP = list()

    def __init__(self, lclreactor):
        APIResource.__init__(self)
        self.reactor = lclreactor

        self.clientFailures = {}

        # Establish the configurer which is the launch point for all chute related endeavors
        self.configurer = configurer.PDConfigurer(None, lclreactor)

        # Pass the configurer off to the API bridge so that WAMP calls can use it.
        apibridge.APIBridge.setConfigurer(self.configurer)

        # Allow each module to register their API calls
        apichute.ChuteAPI(self)
        apiconfig.ConfigAPI(self)
        apistatus.StatusAPI(self)

        # Store failure information for default method.
        self.defaultFailures = dict()

    def _complete(self, update):
        """
        THREADED:call from event thread
        All API operations require some work to happen outside of the API module, therefore 
        when a request comes in we tell it to wait a minute (a NOT_DONE_YET return) and then
        later on we use the reference we have to the request from @update to write the response
        back to the user and close the connection.

        :param name: update
        :param type: UpdateObject
        """
        # Wrap in a try-catch, if the connection is closed by the client before
        # we have a chance to write out our results then this below will result
        # in an exception being raised
        try:
            update.pkg.request.write(json2str(update.result))
            update.pkg.request.finish()

        # TODO don't catch all exceptions here
        except Exception as e:
            pass

    def complete(self, update):
        """
        Kicks off the properly threaded call to complete the API call that was passed
        to PDConfigurer. Since the PDConfigurer module has its own thread that runs outside
        of the main event loop, we have to call back into the event system properly in order
        to keep any issues of concurrency at bay.
        """
        self.reactor.callFromThread(self._complete, update)

    def preprocess(self, request, checkThresh, tictoc):
        """
            Check if failure attempts for the user name has met the threshold.
            Arguments:
                request      : 
                checkThresh  : If None, no checking. Tuple of arguments for checking thresholds
                    ip: IP of client in string format
                    token: sessionToken if found, or None
                    username: username if signin, or None
                    failureDict: the dict for failure history
                ticktoc: If none, do not track the usage. The start time of the API call
            Return:
                str: if threshold is met
                None: if ok
        """

        if(checkThresh):
            ip, token, key, failureDict = checkThresh

            # Check if IP is in whitelist
            ipaddr = apiutils.unpackIPAddr(ip)
            for ipnet in self.WHITELIST_IP:
                net = apiutils.unpackIPAddrWithSlash(ipnet)
                if(apiutils.addressInNetwork(ipaddr, net)):
                    out.verbose('Request from white list: %s\n' % (ip))
                    return None

            if(key in failureDict):
                if(failureDict[key].attempts >= settings.DBAPI_FAILURE_THRESH):
                    out.err('Threshold met: %s %s!\n' % (ip, key))
                    if(tictoc is None):
                        usage = None
                    else:
                        usage = (tictoc, None)
                    self.failprocess(ip, request, (ip, failureDict), None, usage, pdapi.getResponse(pdapi.ERR_THRESHOLD))
                    duration = 0  # self.perf.toc(tictoc)
                    # Log the info of this call
                    # TODO self.usageTracker.addTrackInfo(ip, 'Null', request.path, self.usageTracker.FAIL_THRESH, duration, request.content.getvalue())

                    return "Threshold Met!"
        # Otherwise everything is ok
        return None

    def postprocess(self, request, key, failureDict, logUsage):
        """
            If the client is successful in their request, we should:
            * reset their failure attempts if failureDict is not none.
            * set success response code
            * If usage is not none, add usage track info of the api call
        """
        request.setResponseCode(*pdapi.getResponse(pdapi.OK))
        if(logUsage):
            tictoc, ip, devid = logUsage
            duration = 0  # self.perf.toc(tictoc)
            # when devid is none, we log "Null" into the database
            if(devid is None):
                devid = "Null"
            # Log the info of this call
            # TODO self.usageTracker.addTrackInfo(ip, devid, request.path, self.usageTracker.SUCCESS, duration, request.content.getvalue())
        if(failureDict is not None):
            if(key in failureDict):
                out.info('Clearing %s from failure list\n' % (key))
                del failureDict[key]

    def failprocess(self, ip, request, logFailure, errorStmt, logUsage, errType):
        """
           If logFailure is not None, Update the failureDict when the request does something wrong
           If logUsage is not None, log the usage track info.

           Arguments:
               ip           : IP of client
               request      : the request we received
               logFailure   : If none, we do not log this failure to failure dict. Otherwise it is a tuple of 
                              key          : the key to use in the failureDict
                              failureDict  : the dict record the failure attempt history
               errorStmt    : A string to return to the user, looks like 'Malformed Body: %s'
                              so that we can add things like "Number of attempts remaining: 2" to the response
               logUsage     : A tuple of (tictoc and devid) used for usage tracker
               errorResponse: The error code to set response code

            Returns:
                String to respond to the client
        """
        time = timeflt()

        # Set the response error code
        if(errType == pdapi.ERR_BADPARAM):
            request.setResponseCode(*pdapi.getResponse(errType, ""))
        else:
            request.setResponseCode(*pdapi.getResponse(errType))

        headers = request.requestHeaders
        if(logUsage is not None):
            tictoc, devid = logUsage

            if(devid is None):
                devid = "Null"
            duration = 0  # self.perf.toc(tictoc)
            # Log the info of this call
            # TODO self.usageTracker.addTrackInfo(ip, devid , request.path, self.usageTracker.FAIL_AUTH, duration, request.content.getvalue())

        if(logFailure is not None):
            key, failureDict = logFailure
            # update the accessInfo
            if(key in failureDict):
                failureDict[key].update(ip, headers, time)
            else:
                failureDict[key] = AccessInfo(ip, headers, time)

            attempts = failureDict[key].attempts
            out.warn('Failure access recorded: %s Attempts: %d\n' % (key, attempts))

            remaining = str(max(0, settings.DBAPI_FAILURE_THRESH - attempts))
            if(errorStmt):
                return errorStmt % ("%s attempts remaining" % remaining)
        if(errorStmt):
            return errorStmt % ("Null")

    @GET('^/v1/test')
    def GET_test(self, request):
        """
        A Simple test method to ping if the API server is working properly.
        """
        request.setHeader('Access-Control-Allow-Origin', settings.PDFCD_HEADER_VALUE)
        ip = apiutils.getIP(request)
        out.info('Test called (%s)\n' % (ip))
        request.setResponseCode(*pdapi.getResponse(pdapi.OK))
        return "SUCCESS\n"

    @ALL('^/')
    def default(self, request):
        """
        A dummy catch for all API calls that are not caught by any other module.
        """

        ip = apiutils.getIP(request)
        uri = request.uri
        method = request.method
        # Response the preflight requests
        if (method == 'OPTIONS'):
            request.setHeader('Access-Control-Allow-Origin', '*')
            request.setHeader('Access-Control-Allow-Methods', 'GET, PUT, POST')
            request.setHeader('Access-Control-Allow-Headers', 'Content-Type')
            request.setResponseCode(*pdapi.getResponse(pdapi.OK))
            return "SUCCESS\n"
        else:
            # Get data about who done it
            out.err("Default caught API call (%s => %s:%s)\n" % (ip, method, uri))

            # TODO: What is this?
            tictoc = None

            # Someone might be trying something bad, track their IP
            res = self.preprocess(request, (ip, None, ip, self.defaultFailures), tictoc)
            if(res):
                return res

            self.failprocess(ip, request, (ip, self.defaultFailures), None, (tictoc, None), pdapi.ERR_BADMETHOD)
            return ""


###############################################################################
# Initialization
###############################################################################

def initializeSystem():
    """
    Perform some initialization steps such as writing important configuration.
    """
    dockerapi.writeDockerConfig()


###############################################################################
# Main function
###############################################################################

def setup(args=None):
    """
    This is the main setup function to establish the TCP listening logic for
    the API server. This code also takes into account development or unit test mode.
    """

    # Setup API server
    api = ParadropAPIServer(reactor)
    site = Site(api, timeout=None)

    if args.local:
        # Disable all corrective actions when in local mode.
        # No one wants his dev machine to reboot suddenly.
        ProcessMonitor.allowedActions = set()

    # Development mode
    if(args and args.development):
        thePort = settings.PDFCD_PORT + 10000
        out.info('Using DEVELOPMENT variables')
        # Disable sending the error traceback to the client
        site.displayTracebacks = True
    elif(args and args.unittest):
        thePort = settings.PDFCD_PORT + 20000
        out.info('Running under unittest mode')
        site.displayTracebacks = True
    else:
        thePort = settings.PDFCD_PORT
        site.displayTracebacks = False
        initializeSystem()

    # Setup the port we listen on
    reactor.listenTCP(thePort, site)

    # Never return from here
    reactor.run()
