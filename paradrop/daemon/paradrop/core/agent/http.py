from __future__ import print_function
import json
import pycurl
import re
import six
import urllib

import twisted
from twisted.internet import reactor, threads
from twisted.internet.defer import Deferred, DeferredLock, DeferredSemaphore
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, FileBodyProducer, HTTPConnectionPool
from twisted.web.http_headers import Headers

from paradrop.base import nexus, settings


class JSONReceiver(Protocol):
    """
    JSON Receiver

    A JSONReceiver object can be used with the twisted HTTP client
    to receive data from a request and provide it to a callback
    function when complete.

    Example (response came from an HTTP request):
    finished = Deferred()
    response.deliverBody(JSONReceiver(finished))
    finished.addCallback(func_that_takes_result)

    Some error conditions will result in the callback firing with a result of
    None.  The receiver needs to check for this.  This seems to occur on 403
    errors where the server does not return any data, but twisted just passes
    us a ResponseDone object the same type as a normal result.
    """
    def __init__(self, response, finished):
        """
        response: a twisted Response object
        finished: a Deferred object
        """
        self.response = response
        self.finished = finished
        self.data = ""

    def dataReceived(self, data):
        """
        internal: handles incoming data.
        """
        self.data += data

    def connectionLost(self, reason):
        """
        internal: handles connection close events.
        """
        if reason.check(twisted.web.client.ResponseDone):
            try:
                result = json.loads(self.data)
            except ValueError:
                result = None

            self.finished.callback(PDServerResponse(self.response, data=result))

        else:
            raise Exception(reason.getErrorMessage())


def urlEncodeParams(data):
    """
    Return data URL-encoded.

    This function specifically handles None and boolean values
    to convert them to JSON-friendly strings (e.g. None -> 'null').
    """
    copy = dict()
    for key, value in six.iteritems(data):
        if value is None:
            copy[key] = 'null'
        elif isinstance(value, bool):
            copy[key] = json.dumps(value)
        else:
            copy[key] = value
    return urllib.urlencode(copy, doseq=True)


class PDServerResponse(object):
    """
    A PDServerResponse object contains the results of a request to pdserver.

    This wraps twisted.web.client.Response (cannot be subclassed) and exposes
    the same variables in addition to a 'data' variables.  The 'data' variable,
    if not None, is the parsed object from the response body.
    """
    def __init__(self, response, data=None):
        self.version = response.version
        self.code = response.code
        self.phrase = response.phrase
        self.headers = response.headers
        self.length = response.length
        self.success = (response.code >= 200 and response.code < 300)
        self.data = data


class HTTPResponse(object):
    def __init__(self, data=None):
        self.version = None
        self.code = None
        self.phrase = None
        self.headers = dict()
        self.length = None
        self.success = False
        self.data = data


class HTTPRequestDriver(object):
    def __init__(self):
        self.headers = {
            "Accept": "application/json",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": "ParaDrop/2.5"
        }

    def request(self, method, url, body):
        raise Exception("Not implemented")

    def setHeader(self, key, value):
        self.headers[key] = value


class CurlRequestDriver(HTTPRequestDriver):
    # Shared curl handle.
    # May have problems due to issue #411.
    # https://github.com/pycurl/pycurl/issues/411
    curl = pycurl.Curl()

    # Lock for the access to curl.
    lock = DeferredLock()

    code_pattern = re.compile("(HTTP\S*)\s+(\d+)\s+(.*)")
    header_pattern = re.compile("(\S+): (.*)")

    def __init__(self):
        super(CurlRequestDriver, self).__init__()

        # Buffer for receiving response.
        self.buffer = six.StringIO()

        # Fill in response object.
        self.response = HTTPResponse()

    def receive(self, ignore):
        """
        Receive response from curl and convert it to a response object.
        """
        data = self.buffer.getvalue()

        response = self.response

        # Try to parse the content if it's JSON.
        contentType = response.headers.get('content-type', 'text/html')
        if 'json' in contentType:
            try:
                response.data = json.loads(data)
            except Exception:
                print("Failed to parse JSON")
                print(data)
                response.data = data
        else:
            response.data = data

        response.success = (response.code >= 200 and response.code < 300)
        return response

    def receiveHeaders(self, header_line):
        header_line = header_line.strip()

        match = CurlRequestDriver.code_pattern.match(header_line)
        if match is not None:
            self.response.version = match.group(1)
            self.response.code = int(match.group(2))
            self.response.phrase = match.group(3)
            return

        match = CurlRequestDriver.header_pattern.match(header_line)
        if match is not None:
            key = match.group(1).lower()
            self.response.headers[key] = match.group(2)

    def request(self, method, url, body=None):
        def makeRequest(ignored):
            curl = CurlRequestDriver.curl
            curl.reset()

            curl.setopt(pycurl.URL, url)
            curl.setopt(pycurl.HEADERFUNCTION, self.receiveHeaders)
            curl.setopt(pycurl.WRITEFUNCTION, self.buffer.write)

            curl.setopt(pycurl.CUSTOMREQUEST, method)

            if body is not None:
                curl.setopt(pycurl.POSTFIELDS, body)

            headers = []
            for key, value in six.iteritems(self.headers):
                headers.append("{}: {}".format(key, value))
            curl.setopt(pycurl.HTTPHEADER, headers)

            d = threads.deferToThread(curl.perform)
            d.addCallback(self.receive)
            return d

        def releaseLock(result):
            CurlRequestDriver.lock.release()

            # Forward the result to the next handler.
            return result

        d = CurlRequestDriver.lock.acquire()

        # Make the request once we acquire the semaphore.
        d.addCallback(makeRequest)

        # Release the semaphore regardless of how the request goes.
        d.addBoth(releaseLock)
        return d


class TwistedRequestDriver(HTTPRequestDriver):
    # Using a connection pool enables persistent connections, so we can avoid
    # the connection setup overhead when sending multiple messages to the
    # server.
    pool = HTTPConnectionPool(reactor, persistent=True)

    # Used to control the number of concurrent requests because
    # HTTPConnectionPool does not do that on its own.
    # Discussed here:
    # http://stackoverflow.com/questions/25552432/how-to-make-pooling-http-connection-with-twisted
    sem = DeferredSemaphore(settings.PDSERVER_MAX_CONCURRENT_REQUESTS)

    def receive(self, response):
        """
        Receive response from twisted web client and convert it to a
        PDServerResponse object.
        """
        deferred = Deferred()
        response.deliverBody(JSONReceiver(response, deferred))
        return deferred

    def request(self, method, url, body=None):
        def makeRequest(ignored):
            bodyProducer = None
            if body is not None:
                bodyProducer = FileBodyProducer(six.StringIO(body))

            headers = {}
            for key, value in six.iteritems(self.headers):
                headers[key] = [value]

            agent = Agent(reactor, pool=TwistedRequestDriver.pool)
            d = agent.request(method, url, Headers(headers), bodyProducer)
            d.addCallback(self.receive)
            return d

        def releaseSemaphore(result):
            TwistedRequestDriver.sem.release()

            # Forward the result to the next handler.
            return result

        d = TwistedRequestDriver.sem.acquire()

        # Make the request once we acquire the semaphore.
        d.addCallback(makeRequest)

        # Release the semaphore regardless of how the request goes.
        d.addBoth(releaseSemaphore)
        return d


class PDServerRequest(object):
    """
    Make an HTTP request to pdserver.

    The API is assumed to use application/json for sending and receiving data.
    Authentication is automatically handled here if the router is provisioned.

    We handle missing, invalid, or expired tokens by making the request and
    detecting a 401 (Unauthorized) response.  We request a new token and retry
    the failed request.  We do this at most once and return failure if the
    second attempt returns anything other than 200 (OK).

    PDServerRequest objects are not reusable; create a new one for each
    request.

    URL String Substitutions:
    router_id -> router id

    Example:
    /routers/{router_id}/states -> /routers/halo06/states
    """

    # Auth token (JWT): we will automatically request as needed (for the first
    # request and after expiration) and store the token in memory for future
    # requests.
    token = None

    def __init__(self, path, driver=TwistedRequestDriver, headers={}, setAuthHeader=True):
        self.path = path
        self.driver = driver
        self.headers = headers
        self.setAuthHeader = setAuthHeader
        self.transportRetries = 0

        url = nexus.core.info.pdserver
        if not path.startswith('/'):
            url += '/'
        url += path

        # Perform string substitutions.
        self.url = url.format(router_id=nexus.core.info.pdid)

        self.body = None

    def get(self, **query):
        self.method = 'GET'
        if len(query) > 0:
            self.url += '?' + urlEncodeParams(query)
        d = self.request()
        d.addCallback(self.receiveResponse)
        return d

    def patch(self, *ops):
        """
        Expects a list of operations in jsonpatch format (http://jsonpatch.com/).

        An example operation would be:
        {'op': 'replace', 'path': '/completed', 'value': True}
        """
        self.method = 'PATCH'
        self.body = json.dumps(ops)
        d = self.request()
        d.addCallback(self.receiveResponse)
        return d

    def post(self, **data):
        self.method = 'POST'
        self.body = json.dumps(data)
        d = self.request()
        d.addCallback(self.receiveResponse)
        return d

    def put(self, **data):
        self.method = 'PUT'
        self.body = json.dumps(data)
        d = self.request()
        d.addCallback(self.receiveResponse)
        return d

    def request(self):
        driver = self.driver()
        if self.setAuthHeader and PDServerRequest.token is not None:
            auth = 'Bearer {}'.format(PDServerRequest.token)
            driver.setHeader('Authorization', auth)
        for key, value in six.iteritems(self.headers):
            driver.setHeader(key, value)
        return driver.request(self.method, self.url, self.body)

    def receiveResponse(self, response):
        """
        Intercept the response object, and if it's a 401 authenticate and retry.
        """
        if response.code == 401 and self.setAuthHeader:
            # 401 (Unauthorized) may mean our token is no longer valid.
            # Request a new token and then retry the request.
            #
            # Watch out for infinite recursion here!  If this inner request
            # returns a 401 code, meaning the id/password is invalid, it should
            # not go down this code path again (prevented by check against
            # self.setAuthHeader above).
            authRequest = PDServerRequest('/auth/router', driver=self.driver,
                    setAuthHeader=False)
            d = authRequest.post(id=nexus.core.info.pdid,
                    password=nexus.core.getKey('apitoken'))

            def cbLogin(authResponse):
                if authResponse.success:
                    PDServerRequest.token = authResponse.data.get('token', None)

                    # Retry the original request now that we have a new token.
                    return self.request()

                else:
                    # Our attempt to get a token failed, so give up.
                    return PDServerResponse(response)

            d.addCallback(cbLogin)
            return d

        else:
            return response

    @classmethod
    def getServerInfo(c):
        """
        Return the information needed to send API messages to the server.

        This can be used by an external program (e.g. pdinstall).
        """
        info = {
            'authorization': 'Bearer {}'.format(c.token),
            'router_id': nexus.core.info.pdid,
            'server': nexus.core.info.pdserver
        }
        return info

    @classmethod
    def resetToken(c):
        """
        Reset the auth token, to be called if the router's identity has changed.
        """
        c.token = None


# Initialize pycurl.  Does this do anything?
pycurl.global_init(pycurl.GLOBAL_ALL)


# Set the number of connections that can be kept alive in the connection pool.
# Setting this equal to the size of the semaphore should prevent churn.
TwistedRequestDriver.pool.maxPersistentPerHost = settings.PDSERVER_MAX_CONCURRENT_REQUESTS
