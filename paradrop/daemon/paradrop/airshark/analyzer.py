from twisted.internet.protocol import ProcessProtocol

class AnalyzerProtocol(ProcessProtocol):
    def __init__(self):
        self.ready = False

    def connectionMade(self):
        self.ready = True

    def childDataReceived(self, childFd, data):
        pass

    def processEnded(self, status):
        self.ready = False

    def feedSpectrumData(self, data):
        self.transport.writeToChild(3, data)
