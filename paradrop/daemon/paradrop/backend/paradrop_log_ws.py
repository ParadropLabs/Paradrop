from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
import smokesignal

from paradrop.base.output import out

class ParadropLogWsProtocol(WebSocketServerProtocol):
    def __init__(self, factory):
        WebSocketServerProtocol.__init__(self)
        self.factory = factory

    def onOpen(self):
        out.info('ws /paradrop_logs connected')
        self.factory.addParadropLogObserver(self)

    def onParadropLog(self, logDict):
        self.sendMessage(logDict['message'])

    def onClose(self, wasClean, code, reason):
        out.info('ws /paradrop_logs disconnected: {}'.format(reason))
        self.factory.removeParadropLogObserver(self)


class ParadropLogWsFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        WebSocketServerFactory.__init__(self, *args, **kwargs)
        self.observers = []

    def buildProtocol(self, addr):
        return ParadropLogWsProtocol(self)

    def addParadropLogObserver(self, observer):
        if (self.observers.count(observer) == 0):
            self.observers.append(observer)
            if len(self.observers) == 1:
                smokesignal.on('logs', self.onParadropLog)

    def removeParadropLogObserver(self, observer):
        if (self.observers.count(observer) == 1):
            self.observers.remove(observer)
            if len(self.observers) == 0:
                smokesignal.disconnect(self.onParadropLog)

    def onParadropLog(self, logDict):
        for observer in self.observers:
            observer.onParadropLog(logDict)
