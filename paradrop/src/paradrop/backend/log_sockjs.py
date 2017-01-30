import json
from twisted.internet.protocol import Protocol, Factory

from paradrop.base.output import out
from paradrop.core.container.log_provider import LogProvider


class LogSockJSProtocol(Protocol):
    def __init__(self, factory, log_provider):
        self.factory = factory
        self.log_provider = log_provider

        self.queue = None
        self.queueDeferred = None

    def connectionMade(self):
        if not hasattr(self.factory, "transports"):
            self.factory.transports = set()
        self.factory.transports.add(self.transport)
        out.info('sockjs /logs connected')

        self.connected = True
        self.queue = self.log_provider.attach()

        self.queueDeferred = self.queue.get()
        self.queueDeferred.addCallback(self.sendLogMessage)

    def sendLogMessage(self, msg):
        self.transport.write(json.dumps(msg))

        # Repeat with the next message from the queue.
        self.queueDeferred = self.queue.get()
        self.queueDeferred.addCallback(self.sendLogMessage)

    def connectionLost(self, reason):
        self.factory.transports.remove(self.transport)
        out.info('sockjs /logs disconnected')

        self.connected = False
        self.log_provider.detach()

        # If there is a Deferred waiting for the next message, cancel it.
        if self.queueDeferred is not None:
            self.queueDeferred.cancel()


class LogSockJSFactory(Factory):
    def __init__(self, chutename):
        self.chutename = chutename
        self.transports = set()

    def buildProtocol(self, addr):
        log_provider = LogProvider(self.chutename)
        return LogSockJSProtocol(self, log_provider)
