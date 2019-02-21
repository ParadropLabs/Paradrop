import json

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory

from paradrop.base.output import out


class StatusSockJSProtocol(WebSocketServerProtocol):
    def __init__(self, factory):
        WebSocketServerProtocol.__init__(self)
        self.factory = factory

    def onOpen(self):
        out.info('sockjs /status connected')

    def onMessage(self, data, isBinary):
        if (data == 'refresh'):
            status = self.factory.system_status.getStatus()
            self.sendMessage(json.dumps(status))

    def onClose(self, wasClean, code, reason):
        out.info('sockjs /status disconnected')


class StatusSockJSFactory(WebSocketServerFactory):
    def __init__(self, system_status):
        WebSocketServerFactory.__init__(self)
        self.system_status = system_status

    def buildProtocol(self, addr):
        return StatusSockJSProtocol(self)
