import json

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory

from paradrop.base.output import out


class StatusSockJSProtocol(WebSocketServerProtocol):
    def __init__(self, factory):
        WebSocketServerProtocol.__init__(self)
        self.factory = factory

    def connectionMade(self):
        self.factory.transports.add(self.transport)
        out.info('sockjs /status connected')

    def dataReceived(self, data):
        if (data == 'refresh'):
            status = self.factory.system_status.getStatus()
            self.transport.write(json.dumps(status))

    def connectionLost(self, reason):
        if self.transport in self.factory.transports:
            self.factory.transports.remove(self.transport)
        out.info('sockjs /status disconnected')


class StatusSockJSFactory(WebSocketServerFactory):
    def __init__(self, system_status):
        WebSocketServerFactory.__init__(self)
        self.system_status = system_status
        self.transports = set()

    def buildProtocol(self, addr):
        return StatusSockJSProtocol(self)
