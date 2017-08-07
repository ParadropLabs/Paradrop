import json
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.task import LoopingCall

from paradrop.base.output import out

class AirsharkSpectrumSockJSProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.transports.add(self.transport)
        out.info('sockjs /airshark/spectrum connected')
        self.factory.airshark_manager.add_spectrum_observer(self)

    def on_spectrum_data(self, data):
        self.transport.write(data)

    def connectionLost(self, reason):
        if self.transport in self.factory.transports:
            self.factory.transports.remove(self.transport)
        out.info('sockjs /airshark/spectrum disconnected')
        self.factory.airshark_manager.remove_spectrum_observer(self)


class AirsharkSpectrumSockJSFactory(Factory):
    def __init__(self, airshark_manager):
        self.transports = set()
        self.airshark_manager = airshark_manager

    def buildProtocol(self, addr):
        return AirsharkSpectrumSockJSProtocol(self)


class AirsharkAnalyzerSockJSProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.transports.add(self.transport)
        out.info('sockjs /airshark/analyzer connected')
        self.factory.airshark_manager.add_analyzer_observer(self)

    def on_analyzer_message(self, message):
        # The message is in json format
        self.transport.write(message)

    def connectionLost(self, reason):
        if self.transport in self.factory.transports:
            self.factory.transports.remove(self.transport)
        out.info('sockjs /airshark/analyzer disconnected')
        self.factory.airshark_manager.remove_analyzer_observer(self)


class AirsharkAnalyzerSockJSFactory(Factory):
    def __init__(self, airshark_manager):
        self.transports = set()
        self.airshark_manager = airshark_manager

    def buildProtocol(self, addr):
        return AirsharkAnalyzerSockJSProtocol(self)
