'''
Get system running status including CPU load, memory usage, network traffic.
'''
import psutil
import time

class SystemStatus(object):

    def __init__(self):
        self.timestamp = time.time()
        self.cpu_load = []
        self.mem = dict(total = 0,
                        available = 0,
                        free = 0,
                        cached = 0,
                        buffers = 0)
        self.disk_partitions = {}
        self.network = {}

        included_partitions = set(['/', '/writable'])
        partitions = psutil.disk_partitions()
        for p in partitions:
            if p.fstype == 'ext4' and p.mountpoint in included_partitions:
                usage = psutil.disk_usage(p.mountpoint)
                self.disk_partitions[p.mountpoint] = {
                    'total': usage.total,
                    'used': usage.used
                }        


    def getStatus(self, max_age=0.8):
        """
        Get current system status.

        max_age: maximum tolerable age of cached status information.  Set to
        None to force a refresh regardless of cache age.

        Returns a dictionary with fields 'cpu_load', 'mem', 'disk', and
        'network'.
        """
        timestamp = time.time()
        if (max_age is None or timestamp > self.timestamp + max_age):
            self.timestamp = timestamp
            self.refreshCpuLoad()
            self.refreshMemoryInfo()
            self.refreshDiskInfo()
            self.refreshNetworkTraffic()

        result = {
            'cpu_load': self.cpu_load,
            'mem': self.mem,
            'disk': self.disk_partitions,
            'network': self.network
        }
        return result


    def refreshCpuLoad(self):
        self.cpu_load = map(int, psutil.cpu_percent(percpu=True))


    def refreshMemoryInfo(self):
        mem = psutil.virtual_memory()
        self.mem['total'] = mem.total
        self.mem['available'] = mem.available
        self.mem['free'] = mem.free
        self.mem['cached'] = mem.cached
        self.mem['buffers'] = mem.buffers


    def refreshDiskInfo(self):
        for key, value in self.disk_partitions.iteritems():
            usage = psutil.disk_usage(key)
            self.disk_partitions[key]['total'] = usage.total
            self.disk_partitions[key]['used'] = usage.used


    def refreshNetworkTraffic(self):
        excluded_interfaces = set(["lo", 'br-lan', 'docker0', 'wlan0'])
        interfaces = {}

        stats = psutil.net_if_stats()
        for key, value in stats.iteritems():
            if key in excluded_interfaces:
                continue

            # ignore virtual ethernet interfaces
            if key.startswith('veth'):
                continue

            interfaces[key] = {
                'isup': value.isup,
                'speed': value.speed,
                'mtu': value.mtu              
            }

        addresses = psutil.net_if_addrs()
        for key, value in addresses.iteritems():
            if key not in interfaces:
                continue

            for i in value:
                if i.family == 2:
                    interfaces[key]['ipv4'] = i.address
                    interfaces[key]['netmask'] = i.netmask
                elif i.family == 17:
                    interfaces[key]['mac'] = i.address

        traffic = psutil.net_io_counters(pernic=True)
        for key, value in traffic.iteritems():
            if key not in interfaces:
                continue

            interfaces[key]['bytes_sent'] = value.bytes_sent
            interfaces[key]['bytes_recv'] = value.bytes_recv
            interfaces[key]['packets_sent'] = value.packets_sent
            interfaces[key]['packets_recv'] = value.packets_recv
            interfaces[key]['errin'] = value.errin
            interfaces[key]['errout'] = value.errout
            interfaces[key]['dropin'] = value.dropin
            interfaces[key]['dropout'] = value.dropout

        self.network = interfaces
