import json
from twisted.internet.protocol import Protocol, Factory

from paradrop.base.output import out


class LogSockJSProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.queue = factory.log_provider.attach()

    def connectionMade(self):
        if not hasattr(self.factory, "transports"):
            self.factory.transports = set()
        self.factory.transports.add(self.transport)
        out.info('sockjs /status connected')

        d = self.queue.get()
        d.addCallback(self.sendLogMessage)

    def sendLogMessage(self, msg):
        self.transport.write(json.dumps(msg))

    def connectionLost(self, reason):
        self.factory.transports.remove(self.transport)
        out.info('sockjs /status disconnected')


class LogSockJSFactory(Factory):
    def __init__(self, log_provider):
        self.log_provider = log_provider
        self.transports = set()

    def buildProtocol(self, addr):
        return StatusSockJSProtocol(self)
