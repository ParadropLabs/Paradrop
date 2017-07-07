import json
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.task import LoopingCall

from paradrop.base.output import out

class AirsharkSockJSProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        if not hasattr(self.factory, "transports"):
            self.factory.transports = set()
        self.factory.transports.add(self.transport)
        out.info('sockjs /airshark connected')
        self.factory.airshark_manager.add_observer(self)

    def on_spectrum_data(self, tsf, freq, noise, rssi, pwr):
        self.transport.write(json.dumps({'tsf': tsf, 'freq': freq, 'noise': noise, 'rssi': rssi, 'pwr': pwr}))

    def connectionLost(self, reason):
        self.factory.transports.remove(self.transport)
        out.info('sockjs /airshark disconnected')
        self.factory.airshark_manager.remove_observer(self)


class AirsharkSockJSFactory(Factory):
    def __init__(self, airshark_manager):
        self.transports = set()
        self.airshark_manager = airshark_manager

    def buildProtocol(self, addr):
        return AirsharkSockJSProtocol(self)
