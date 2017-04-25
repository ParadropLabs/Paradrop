import os
import re
import signal
import subprocess

from paradrop.base import settings
from paradrop.base.output import out
from paradrop.core.config import devices
from paradrop.lib.utils import datastruct, pdosq


def findInterfaceFromMAC(mac):
    """
    Find the name of an interface with the given MAC address.
    """
    mac = mac.lower()

    dname = '/sys/class/net'
    for ifname in os.listdir(dname):
        path = os.path.join(dname, ifname, 'address')
        with open(path, 'r') as source:
            addr = source.read().strip()
            if addr == mac:
                return ifname

    return None


def airsharkInstalled():
    """
    Test if Airshark is installed.
    """
    return os.path.exists(settings.AIRSHARK_INSTALL_DIR)


class AirsharkManager(object):
    def __init__(self):
        self.pidDir = os.path.join(settings.RUNTIME_HOME_DIR, 'airshark')
        pdosq.makedirs(self.pidDir)

    def getActiveInterfaces(self):
        """
        Return list of interfaces with Airshark running.
        """
        try:
            return os.listdir(self.pidDir)
        except OSError:
            return []

    def getPidPath(self, interface):
        """
        Get the path where the PID file should go.
        """
        fname = '{}.pid'.format(interface)
        return os.path.join(self.pidDir, fname)

    def setActive(self, interfaces):
        """
        Set a new list of active interfaces.

        Stop Airshark from running on any removed interfaces, and start
        Airshark on any added interfaces.
        """
        old_interfaces = set(self.getActiveInterfaces())
        new_interfaces = set(interfaces)

        for ifname in (old_interfaces - new_interfaces):
            self.stop(ifname)

        for ifname in (new_interfaces - old_interfaces):
            self.start(ifname)

    def start(self, interface):
        """
        Start Airshark on a given interface.
        """
        cmd = [os.path.join(settings.AIRSHARK_INSTALL_DIR, 'run_airshark.sh'),
                interface]
        env = {
            'SNAP': settings.AIRSHARK_INSTALL_DIR
        }
        proc = subprocess.Popen(cmd, env=env)
        with open(self.getPidPath(), 'w') as output:
            output.write('{}'.format(proc.pid))

    def stop(self, interface):
        """
        Stop Airshark on a given interface.
        """
        with open(self.getPidPath(), 'r') as source:
            pid = int(source.read().strip())
        os.kill(pid, signal.SIGKILL)


def configure(update):
    hostConfig = update.new.getCache('hostConfig')
    networkDevices = update.new.getCache('networkDevices')

    interfaces = hostConfig.get('wifi-interfaces', [])
    shark_interfaces = []

    # Look for objects in wifi-interfaces with mode == 'airshark'.
    for interface in interfaces:
        if interface.get('mode', None) != 'airshark':
            continue

        device = devices.resolveWirelessDevRef(interface['device'],
                networkDevices)
        if device['primary_interface'] is not None:
            shark_interfaces.append(device['primary_interface'])

    # Give a helpful error if user tried to configure Airshark, but it is not
    # installed.
    if len(shark_interfaces) > 0 and not airsharkInstalled():
        raise Exception("Airshark is not installed.")

    manager = AirsharkManager()
    manager.setActive(shark_interfaces)
