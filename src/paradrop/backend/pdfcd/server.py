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

from paradrop.lib.utils.output import out, logPrefix
from paradrop.lib.utils.pdutils import timeflt, str2json, json2str
from paradrop.lib.api import pdapi
from paradrop.lib.api import pdrest
from paradrop.lib import settings

from paradrop.backend.pdfcd import apiutils
from paradrop.backend.pdfcd import apichute


###########################################################################################################################
# API Callbacks
###########################################################################################################################
class ParadropAPIServer(pdrest.APIResource):
    def __init__(self, lclreactor):
        pdrest.APIResource.__init__(self)
        self.reactor = lclreactor

        # Allow each module to register their API calls
        apichute.ChuteAPI(self)


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
                if(apiutils.addressInNetwork(ipaddr, ipnet)):
                    out.verbose('-- %s Request from white list: %s\n' % (logPrefix(), ip))
                    return None

            if(key in failureDict):
                if(failureDict[key].attempts >= settings.DBAPI_FAILURE_THRESH):
                    out.err('!! %s Threshold met: %s %s!\n' % (logPrefix(), ip, key))
                    if(tictoc is None):
                        usage = None
                    else:
                        usage = (tictoc, None)
                    self.failprocess(ip, request, (ip, self.clientFailures), None, usage, pdapi.getResponse(pdapi.ERR_THRESHOLD))
                    duration = self.perf.toc(tictoc)
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
            duration = self.perf.toc(tictoc)
            # when devid is none, we log "Null" into the database
            if(devid is None):
                devid = "Null"
            # Log the info of this call
            # TODO self.usageTracker.addTrackInfo(ip, devid, request.path, self.usageTracker.SUCCESS, duration, request.content.getvalue())
        if(failureDict is not None):
            if(key in failureDict):
                out.info('-- %s Clearing %s from failure list\n' % (logPrefix(), key))
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
        
        headers = request.received_headers
        if(logUsage is not None):
            tictoc, devid = logUsage

            if(devid is None):
                devid = "Null"
            duration = self.perf.toc(tictoc)
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
            out.warn('** %s Failure access recorded: %s Attempts: %d\n' % (logPrefix(), key, attempts))

            remaining = str(max(0, settings.DBAPI_FAILURE_THRESH - attempts))
            if(errorStmt):
                return errorStmt % ("%s attempts remaining" % remaining)
        if(errorStmt):
            return errorStmt % ("Null")



    @pdrest.GET('^/v1/test')
    def GET_test(self, request):
        request.setHeader('Access-Control-Allow-Origin', settings.PDFCD_HEADER_VALUE)
        ip = apiutils.getIP(request)
        out.info('-- %s Test called (%s)\n' % (logPrefix(), ip))
        request.setResponseCode(*pdapi.getResponse(pdapi.OK))
        return "SUCCESS\n"
    
    @pdrest.ALL('^/')
    def default(self, request):
        ip = apiutils.getIP(request)
        uri = request.uri
        method = request.method
        # Get data about who done it
        out.err("!! %s Default caught API call (%s => %s:%s)\n" % (logPrefix(), ip, method, uri))
        
        # Someone might be trying something bad, track their IP
        res = self.preprocess(request, (ip, None, ip, self.defaultFailures), tictoc)
        if(res):
            return res
        
        self.failprocess(ip, request, (ip, self.defaultFailures), None, (tictoc, None), pdapi.ERR_BADMETHOD)
        return ""
        

       
###############################################################################
# Main function
###############################################################################
def setup(args=None):
    
    # Setup API server
    api = ParadropAPIServer(reactor)
    site = Site(api, timeout=None)
    
    # Development mode
    if(args and args.development):
        thePort = settings.PDFCD_PORT + 10000
        out.info('-- %s Using DEVELOPMENT variables\n' % (logPrefix()))
        # Disable sending the error traceback to the client
        site.displayTracebacks = True
    elif(args and args.unittest):
        thePort = settings.DBAPI_PORT + 20000
        out.info('-- %s Running under unittest mode\n' % (logPrefix())) 
        site.displayTracebacks = True
    else:
        thePort = settings.PDFCD_PORT
        site.displayTracebacks = False
        
    # Setup the port we listen on
    out.info('-- %s Establishing API server, port: %d\n' % (logPrefix(), thePort))
    reactor.listenTCP(thePort, site)

    # Never return from here
    reactor.run()
       
