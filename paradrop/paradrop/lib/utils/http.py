import base64
import json

import twisted
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol

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
    def __init__(self, finished):
        """
        finished: a Deferred object
        """
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
            self.finished.callback(result)
        else:
            raise Exception(reason.getErrorMessage())


def getAPIToken():
    """
    Get the API token.

    This is currently stored in a file called 'apitoken' under the configured
    keys directory.

    Returns None if the file does not exist.
    """
    return nexus.core.getKey('apitoken')


def buildAuthString():
    """
    Use the pdid and API token to construct a string for an HTTP Authorization
    header.

    Example:
    "Basic <base64 representation of pdid:token>"
    """
    basic = "{}:{}".format(nexus.core.info.pdid, getAPIToken())
    b64value = base64.b64encode(basic)
    return "Basic {}".format(b64value)
