from twisted.internet.task import LoopingCall

from paradrop.base import settings
from paradrop.lib.utils import pdos
from paradrop.core.config.airshark import airshark_interface_manager
from scanner import Scanner
from spectrum_reader import SpectrumReader

class AirsharkManager(object):
    def __init__(self):
        self.loop = LoopingCall(self.check_spectrum)
        self.wifi_interface = None
        self.scanner = None
        self.observers = []

        airshark_interface_manager.add_observer(self)

    def status(self):
        hardware_ready = False
        software_ready = False
        scanner_running = False
        if self.wifi_interface:
            hardware_ready = True

        if pdos.exists(settings.AIRSHARK_INSTALL_DIR):
            software_ready = True

        if self.scanner:
            scanner_running = True

        return (hardware_ready, software_ready, scanner_running)

    def on_interface_up(self, interface):
        self.stop()
        self.wifi_interface = interface
        self.start()

    def on_interface_down(self, interface):
        self.wifi_interface = None
        self.stop()

    def start(self):
        if (self.wifi_interface):
            if (self.scanner is None):
                self.scanner = Scanner(self.wifi_interface)
                self.scanner.cmd_chanscan()
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

    def check_spectrum(self):
        ts, data = self.scanner.spectrum_reader.read_samples()
        if (data is not None):
            for (tsf, max_exp, freq, rssi, noise, max_mag, max_index, bitmap_weight, sdata) in SpectrumReader.decode(data):
                for observer in self.observers:
                    observer.on_spectrum_data(tsf, max_exp, freq, rssi, noise, max_mag, max_index, bitmap_weight, sdata)

    # TODO: Not sure we need it or not
    def read_raw_samples(self):
        if (self.scanner):
            return self.scanner.spectrum_reader.read_samples()
        else:
            return None, None

    def add_observer(self, observer):
        if (self.observers.count(observer) == 0):
            self.observers.append(observer)

    def remove_observer(self, observer):
        if (self.observers.count(observer) == 1):
            self.observers.remove(observer)
