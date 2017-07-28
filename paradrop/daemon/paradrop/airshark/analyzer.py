from paradrop.base.output import out

from twisted.internet.protocol import ProcessProtocol

class AnalyzerProcessProtocol(ProcessProtocol):
    def __init__(self):
        self.ready = False

    def isRunning(self):
        return self.ready

    def connectionMade(self):
        self.ready = True
        out.info('Airshark analyzer process starts')

    def childDataReceived(self, childFd, data):
        pass

    def processEnded(self, status):
        self.ready = False
        out.info('Airshark analyzer process exits')

    def feedSpectrumData(self, data):
        self.transport.writeToChild(3, data)

    def stop(self):
        self.transport.signalProcess('KILL')
