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
            # Output of airshark analyzer
            #out.info(data)
            self.airshark_manager.on_analyzer_message(data)
        elif (childFd == 1 or childFd == 2):
            # stdout/stderr of airshark analyzer
            out.info('Airshark: ========\n%s==================' % data)

    def processEnded(self, status):
        out.info('Airshark analyzer process exits')
        self.ready = False

    def feedSpectrumData(self, data):
        self.transport.writeToChild(3, data)

    def stop(self):
        self.transport.signalProcess('KILL')
