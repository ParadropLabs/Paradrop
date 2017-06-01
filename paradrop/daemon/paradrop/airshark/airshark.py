from twisted.internet.task import LoopingCall

from paradrop.core.config import airshark
from scanner import Scanner
from spectrum_reader import SpectrumReader

class AirsharkManager(object):
    def __init__(self):
        self.loop = LoopingCall(self.check_result)
        self.scanner = None
        self.observers = []

    def start(self):
        if (airshark.wifi_interface):
            if (self.scanner is None):
                self.scanner = Scanner(airshark.wifi_interface)
                self.scanner.start()
                self.loop.start(0.1)
            return True
        else:
            return False

    def stop(self):
        if (self.scanner):
            self.scanner.stop()
            self.scanner = None
            self.loop.stop()

    def get_status(self):
        if (self.scanner):
            return True
        else:
            return False

    def check_result(self):
        ts, data = self.scanner.spectrum_reader.read_samples()
        if (data is not None):
            for (tsf, freq, noise, rssi, pwr) in SpectrumReader.decode(data):
                for observer in self.observers:
                    observer.on_new_samples(tsf, freq, noise, rssi, pwr)

    # TODO: Not sure we need it or not
    def read_raw_samples(self):
        if (self.scanner):
            return self.scanner.spectrum_reader.read_samples()
        else:
            return None, None

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)
