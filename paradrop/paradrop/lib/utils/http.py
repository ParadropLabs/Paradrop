import base64
import json
import urllib

from cStringIO import StringIO

import twisted
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, FileBodyProducer, Response
from twisted.web.http_headers import Headers

from paradrop.lib import settings
from pdtools.lib import nexus


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
    for key, value in data.iteritems():
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
        self.success = (response.code == 200)
        self.data = data


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
    """

    # Auth token (JWT): we will automatically request as needed (for the first
    # request and after expiration) and store the token in memory for future
    # requests.
    token = None

    def __init__(self, path, auth=True):
        self.path = path

        self.url = settings.PDSERVER_URL
        if not path.startswith('/'):
            self.url += '/'
        self.url += path

        self.headers = Headers({
            'Accept': ['application/json'],
            'Content-Type': ['application/json'],
            'User-Agent': ['ParaDrop/2.5']
        })

        if auth and PDServerRequest.token is not None:
            auth = 'Bearer {}'.format(PDServerRequest.token)
            self.headers.setRawHeaders('Authorization', [auth])

        self.body = None

        # This will be returned to the caller to wait for the response.
        self.deferred = Deferred()

    def get(self, **query):
        self.method = 'GET'

        if len(query) > 0:
            self.url += '?' + urlEncodeParams(query)

        d = self.request()
        d.addCallback(self.receiveResponse)

        return self.deferred

    def post(self, **data):
        self.method = 'POST'

        datastr = json.dumps(data)
        self.body = FileBodyProducer(StringIO(datastr))

        d = self.request()
        d.addCallback(self.receiveResponse)

        return self.deferred

    def put(self, **data):
        self.method = 'PUT'

        datastr = json.dumps(data)
        self.body = FileBodyProducer(StringIO(datastr))

        d = self.request()
        d.addCallback(self.receiveResponse)

        return self.deferred

    def request(self):
        agent = Agent(reactor)
        d = agent.request(self.method, self.url, self.headers, self.body)
        return d

    def receiveResponse(self, response):
        if response.code in [401, 403]:
            # 401 (Unauthorized) may mean our token is no longer valid.
            # Request a new token and then retry the request.
            #
            # We also detect 403 (Forbidden) here in case the implementation
            # returns that instead of 401.
            authRequest = PDServerRequest('login', auth=False)
            d = authRequest.post(name=nexus.core.info.pdid,
                    password=nexus.core.getKey('apitoken'))

            def cbLogin(authResponse):
                if authResponse.success:
                    PDServerRequest.token = authResponse.data.get('token', None)

                    # Add the new token to our headers.
                    auth = 'Bearer {}'.format(PDServerRequest.token)
                    self.headers.setRawHeaders('Authorization', [auth])

                    # Retry the original request now that we have a new token.
                    d = self.request()
                    d.addCallback(self.receiveRetryResponse)

                else:
                    # Our attempt to get a token failed, so give up.
                    self.deferred.callback(PDServerResponse(response))

            d.addCallback(cbLogin)

        elif response.code == 200:
            # Parse the response and trigger callback when ready.
            response.deliverBody(JSONReceiver(response, self.deferred))

        else:
            self.deferred.callback(PDServerResponse(response))

    def receiveRetryResponse(self, response):
        if response.code == 200:
            # Parse the response and trigger callback when ready.
            response.deliverBody(JSONReceiver(response, self.deferred))
        else:
            self.deferred.callback(PDServerResponse(response))
