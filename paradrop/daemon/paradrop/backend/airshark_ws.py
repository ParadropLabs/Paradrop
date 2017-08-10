from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory

from paradrop.base.output import out

class AirsharkSpectrumProtocol(WebSocketServerProtocol):
    def __init__(self, factory):
        WebSocketServerProtocol.__init__(self)
        self.factory = factory

    def onOpen(self):
        out.info('ws /airshark/spectrum connected')
        self.factory.airshark_manager.add_spectrum_observer(self)

    def on_spectrum_data(self, data):
        self.sendMessage(data, True)

    def onClose(self, wasClean, code, reason):
        out.info('ws /airshark/spectrum disconnected: {}'.format(reason))
        self.factory.airshark_manager.remove_spectrum_observer(self)


class AirsharkSpectrumFactory(WebSocketServerFactory):
    def __init__(self, airshark_manager, *args, **kwargs):
        WebSocketServerFactory.__init__(self, *args, **kwargs)
        self.airshark_manager = airshark_manager

    def buildProtocol(self, addr):
        return AirsharkSpectrumProtocol(self)


class AirsharkAnalyzerProtocol(WebSocketServerProtocol):
    def __init__(self, factory):
        WebSocketServerProtocol.__init__(self)
        self.factory = factory

    def onOpen(self):
        out.info('ws /airshark/analyzer connected')
        self.factory.airshark_manager.add_analyzer_observer(self)

    def on_analyzer_message(self, message):
        # The message is in json format
        self.sendMessage(message, False)

    def onClose(self, wasClean, code, reason):
        out.info('ws /airshark/analyzer disconnected: {}'.format(reason))
        self.factory.airshark_manager.remove_analyzer_observer(self)


class AirsharkAnalyzerFactory(WebSocketServerFactory):
    def __init__(self, airshark_manager, *args, **kwargs):
        WebSocketServerFactory.__init__(self, *args, **kwargs)
        self.airshark_manager = airshark_manager

    def buildProtocol(self, addr):
        return AirsharkAnalyzerProtocol(self)
