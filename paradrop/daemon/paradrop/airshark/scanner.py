from __future__ import print_function
from multiprocessing import Process, Value
from ctypes import c_bool
import os
import time

from .spectrum_reader import SpectrumReader

class Scanner(object):
    interface = None
    freqlist = None
    process = None
    debugfs_dir = None
    spectrum_reader = None

    def __init__(self, interface):
        self.interface = interface
        self.phy = ""
        self.debugfs_dir = self._find_debugfs_dir()
        if not self.debugfs_dir:
            raise Exception('Unable to access spectral_scan_ctl file for interface %s' % interface)

        self.ctl_file = '%s/spectral_scan_ctl' % self.debugfs_dir
        self.sample_count_file = '%s/spectral_count' % self.debugfs_dir
        self.short_repeat_file = '%s/spectral_short_repeat' % self.debugfs_dir
        self.cur_chan = 6
        self.sample_count = 8
        self.process = None
        self.set_freqs(2412, 2472, 5)
        self.spectrum_reader = SpectrumReader('%s/spectral_scan0' % self.debugfs_dir)

    def dev_to_phy(self, dev):
        f = open('/sys/class/net/%s/phy80211/name' % dev)
        phy = f.read().strip()
        f.close()
        return phy

    def _find_debugfs_dir(self):
        ''' search debugfs for spectral_scan_ctl for this interface '''
        for dirname, subd, files in os.walk('/sys/kernel/debug/ieee80211'):
            if 'spectral_scan_ctl' in files:
                phy = dirname.split(os.path.sep)[-2]
                if phy == self.dev_to_phy(self.interface):
                    self.phy = phy
                    return dirname
        return None

    def _scan(self, scanning):
        while scanning.value:
            cmd = 'iw dev %s scan trigger' % self.interface
            if self.freqlist:
                cmd = '%s freq %s' % (cmd, ' '.join(self.freqlist))
            os.system('%s >/dev/null 2>/dev/null' % cmd)
            time.sleep(0.1)

    def set_freqs(self, minf, maxf, spacing):
        self.freqlist = ['%s' % x for x in range(minf, maxf + spacing, spacing)]

    def cmd_chanscan(self):
        f = open(self.ctl_file, 'w')
        f.write("chanscan")
        f.close()

    def cmd_disable(self):
        f = open(self.ctl_file, 'w')
        f.write("disable")
        f.close()

    def cmd_set_samplecount(self, count):
        print("set sample count to %d" % count)
        f = open(self.sample_count_file, 'w')
        f.write("%s" % count)
        f.close()

    def cmd_set_short_repeat(self, short_repeat):
        f = open(self.short_repeat_file, 'w')
        f.write("%s" % short_repeat)
        f.close()

    def start(self):
        if self.process is None:
            self.scanning = Value(c_bool, True)
            self.process = Process(target=self._scan, args=(self.scanning,))
            self.process.start()

    def stop(self):
        self.cmd_disable()
        if self.process is not None:
            self.scanning.value = False
            self.process.join()
            self.process = None
            self.spectrum_reader.flush()

    def get_debugfs_dir(self):
        return self.debugfs_dir
