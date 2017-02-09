import json
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.task import LoopingCall

from paradrop.base.output import out
from paradrop.core.container.log_provider import LogProvider

class LogSockJSProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.loop = LoopingCall(self.check_log)

    def connectionMade(self):
        if not hasattr(self.factory, "transports"):
            self.factory.transports = set()
        self.factory.transports.add(self.transport)
        out.info('sockjs /logs connected')

        self.factory.log_provider.attach()
        self.loop.start(1.0)

    def check_log(self):
        logs = self.factory.log_provider.get_logs()
        for log in logs:
            self.transport.write(json.dumps(log))

    def connectionLost(self, reason):
        self.factory.transports.remove(self.transport)
        out.info('sockjs /logs disconnected')

        self.loop.stop()
        self.factory.log_provider.detach()

class LogSockJSFactory(Factory):
    def __init__(self, chutename):
        self.transports = set()
        self.log_provider = LogProvider(chutename)

    def buildProtocol(self, addr):
        return LogSockJSProtocol(self)
