import json

import twisted
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol


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
            self.finished.callback(json.loads(self.data))
        else:
            raise Exception(reason.getErrorMessage())
