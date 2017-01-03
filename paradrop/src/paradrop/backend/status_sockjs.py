import json
from twisted.internet.protocol import Protocol, Factory

from paradrop.base.output import out


class StatusSockJSProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory


    def connectionMade(self):
        if not hasattr(self.factory, "transports"):
            self.factory.transports = set()
        self.factory.transports.add(self.transport)
        out.info('sockjs /status connected')


    def dataReceived(self, data):
        if (data == 'refresh'):
            status = self.factory.system_status.getStatus()
            self.transport.write(json.dumps(status))


    def connectionLost(self, reason):
        self.factory.transports.remove(self.transport)
        out.info('sockjs /status disconnected')


class StatusSockJSFactory(Factory):
    def __init__(self, system_status):
        self.system_status = system_status
        self.transports = set()

    def buildProtocol(self, addr):
        return StatusSockJSProtocol(self)
