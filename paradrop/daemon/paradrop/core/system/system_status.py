'''
Get system running status including CPU load, memory usage, network traffic.
'''
import time

import psutil
import six


class SystemStatus(object):
    INCLUDED_PARTITIONS = set(['/', '/writable'])

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
            if p.mountpoint in self.INCLUDED_PARTITIONS:
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
        self.cpu_load = list(map(int, psutil.cpu_percent(percpu=True)))


    def refreshMemoryInfo(self):
        mem = psutil.virtual_memory()
        self.mem['total'] = mem.total
        self.mem['available'] = mem.available
        self.mem['free'] = mem.free
        self.mem['cached'] = mem.cached
        self.mem['buffers'] = mem.buffers


    def refreshDiskInfo(self):
        for key, value in six.iteritems(self.disk_partitions):
            usage = psutil.disk_usage(key)
            self.disk_partitions[key]['total'] = usage.total
            self.disk_partitions[key]['used'] = usage.used


    def refreshNetworkTraffic(self):
        excluded_interfaces = set(["lo", 'br-lan', 'docker0', 'wlan0'])
        interfaces = {}

        stats = psutil.net_if_stats()
        for key, value in six.iteritems(stats):
            if key in excluded_interfaces:
                continue

            # ignore virtual ethernet interfaces
            if key.startswith('veth'):
                continue

            # Quick fix - ignore interfaces with dots because our server
            # refuses to accept keys with dots.
            if '.' in key:
                continue

            interfaces[key] = {
                'isup': value.isup,
                'speed': value.speed,
                'mtu': value.mtu
            }

        addresses = psutil.net_if_addrs()
        for key, value in six.iteritems(addresses):
            if key not in interfaces:
                continue

            for i in value:
                if i.family == 2:
                    interfaces[key]['ipv4'] = i.address
                    interfaces[key]['netmask'] = i.netmask
                elif i.family == 17:
                    interfaces[key]['mac'] = i.address

        traffic = psutil.net_io_counters(pernic=True)
        for key, value in six.iteritems(traffic):
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

    @classmethod
    def getNetworkInfo(cls):
        interfaces = {}

        stats = psutil.net_if_stats()
        for key, value in six.iteritems(stats):
            interfaces[key] = value.__dict__
            interfaces[key]['addresses'] = []
            interfaces[key]['io_counters'] = None

        addresses = psutil.net_if_addrs()
        for key, value in six.iteritems(addresses):
            if key not in interfaces:
                continue

            for addr in value:
                interfaces[key]['addresses'].append(addr.__dict__)

        traffic = psutil.net_io_counters(pernic=True)
        for key, value in six.iteritems(traffic):
            if key not in interfaces:
                continue

            interfaces[key]['io_counters'] = value.__dict__

        return interfaces

    @classmethod
    def getProcessInfo(cls, pid):
        proc = psutil.Process(pid=pid)
        with proc.oneshot():
            proc_info = {
                'cpu_num': proc.cpu_num(),
                'cpu_times': proc.cpu_times().__dict__,
                'create_time': proc.create_time(),
                'memory_info': proc.memory_info().__dict__,
                'num_ctx_switches': proc.num_ctx_switches().__dict__,
                'num_threads': proc.num_threads()
            }
        return proc_info

    @classmethod
    def getSystemInfo(cls):
        system = {
            'boot_time': psutil.boot_time(),
            'cpu_count': psutil.cpu_count(),
            'cpu_stats': psutil.cpu_stats().__dict__,
            'cpu_times': [k.__dict__ for k in psutil.cpu_times(percpu=True)],
            'disk_io_counters': psutil.disk_io_counters().__dict__,
            'disk_usage': [],
            'net_io_counters': psutil.net_io_counters().__dict__,
            'swap_memory': psutil.swap_memory().__dict__,
            'virtual_memory': psutil.virtual_memory().__dict__
        }

        partitions = psutil.disk_partitions()
        for p in partitions:
            if p.mountpoint in cls.INCLUDED_PARTITIONS:
                usage = psutil.disk_usage(p.mountpoint)
                system['disk_usage'].append({
                    'mountpoint': p.mountpoint,
                    'total': usage.total,
                    'used': usage.used
                })

        return system
