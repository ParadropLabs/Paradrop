import json

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from twisted.internet.task import LoopingCall

from paradrop.base.output import out
from paradrop.core.container.log_provider import LogProvider

class LogSockJSProtocol(WebSocketServerProtocol):
    def __init__(self, factory):
        WebSocketServerProtocol.__init__(self)
        self.factory = factory
        self.loop = LoopingCall(self.check_log)
        self.log_provider = None

    def onOpen(self):
        out.info('sockjs /logs connected')

        self.log_provider = LogProvider(self.factory.chute)
        self.log_provider.attach()
        self.loop.start(1.0)

    def check_log(self):
        logs = self.log_provider.get_logs()
        for log in logs:
            self.sendMessage(json.dumps(log))

    def onClose(self, wasClean, code, reason):
        out.info('sockjs /logs disconnected')

        self.loop.stop()
        self.log_provider.detach()
        self.log_provider = None

class LogSockJSFactory(WebSocketServerFactory):
    def __init__(self, chute):
        WebSocketServerFactory.__init__(self)
        self.chute = chute

    def buildProtocol(self, addr):
        return LogSockJSProtocol(self)
