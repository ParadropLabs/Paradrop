import json
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.task import LoopingCall

from paradrop.base.output import out
from paradrop.core.container.log_provider import LogProvider

class LogSockJSProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.loop = LoopingCall(self.check_log)
        self.log_provider = None

    def connectionMade(self):
        self.factory.transports.add(self.transport)
        out.info('sockjs /logs connected')

        self.log_provider = LogProvider(self.factory.chute_name)
        self.log_provider.attach()
        self.loop.start(1.0)

    def check_log(self):
        logs = self.log_provider.get_logs()
        for log in logs:
            self.transport.write(json.dumps(log))

    def connectionLost(self, reason):
        if self.transport in self.factory.transports:
            self.factory.transports.remove(self.transport)
        out.info('sockjs /logs disconnected')

        self.loop.stop()
        self.log_provider.detach()
        self.log_provider = None

class LogSockJSFactory(Factory):
    def __init__(self, chutename):
        self.transports = set()
        self.chute_name = chutename

    def buildProtocol(self, addr):
        return LogSockJSProtocol(self)
