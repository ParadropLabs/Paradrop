from twisted.internet.protocol import ProcessProtocol
from paradrop.base.output import out

class AnalyzerProcessProtocol(ProcessProtocol):
    def __init__(self, airshark_manager):
        self.ready = False
        self.airshark_manager = airshark_manager

    def isRunning(self):
        return self.ready

    def connectionMade(self):
        out.info('Airshark analyzer process starts')
        self.ready = True

    def childDataReceived(self, childFd, data):
        if (childFd == 4):
            out.info(data)

    def processEnded(self, status):
        out.info('Airshark analyzer process exits')
        self.ready = False
        self.airshark_manager.remove_raw_data_observer(self)

    def feedSpectrumData(self, data):
        self.transport.writeToChild(3, data)

    def stop(self):
        self.transport.signalProcess('KILL')
