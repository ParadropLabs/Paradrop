from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from twisted.internet.task import LoopingCall

from paradrop.base.output import out
from paradrop.core.container.log_provider import LogProvider

class ChuteLogWsProtocol(WebSocketServerProtocol):
    def __init__(self, factory):
        WebSocketServerProtocol.__init__(self)
        self.factory = factory
        self.loop = LoopingCall(self.check_log)
        self.log_provider = None

    def onOpen(self):
        out.info('ws /chute_logs connected')
        self.log_provider = LogProvider(self.factory.chute)
        self.log_provider.attach()
        self.loop.start(0.5)

    def check_log(self):
        logs = self.log_provider.get_logs()
        for log in logs:
            self.sendMessage(log)

    def onClose(self, wasClean, code, reason):
        out.info('ws /chute_logs disconnected: {}'.format(reason))
        self.loop.stop()
        self.log_provider.detach()
        self.log_provider = None


class ChuteLogWsFactory(WebSocketServerFactory):
    def __init__(self, chute, *args, **kwargs):
        WebSocketServerFactory.__init__(self, *args, **kwargs)
        self.chute = chute

    def buildProtocol(self, addr):
        return ChuteLogWsProtocol(self)
