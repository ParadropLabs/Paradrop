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

        partitions = psutil.disk_partitions()
        for p in partitions:
            if p.fstype == 'ext4':
                usage = psutil.disk_usage(p.mountpoint)
                self.disk_partitions[p.mountpoint] = {
                    'total': usage.total,
                    'used': usage.used
                }        


    def getStatus(self):
        timestamp = time.time()
        if (timestamp > self.timestamp + 0.8):
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

            interfaces[key] = {
                'isup': value.isup,
                'speed': value.speed,
                'mtu': value.mtu              
            }

        addresses = psutil.net_if_addrs()
        for key, value in addresses.iteritems():
            if key in excluded_interfaces:
                continue
            for i in value:
                if i.family == 2:
                    interfaces[key]['ipv4'] = i.address
                    interfaces[key]['netmask'] = i.netmask
                elif i.family == 17:
                    interfaces[key]['mac'] = i.address

        traffic = psutil.net_io_counters(pernic=True)
        for key, value in traffic.iteritems():
            if key in excluded_interfaces:
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
