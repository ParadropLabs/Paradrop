import os

from paradrop.core.config import devices


class AirsharkInterfaceManager(object):
    def __init__(self):
        self.interface = None
        self.observers = []

    def interface_available(self):
        return self.interface != None

    def add_observer(self, observer):
        if self.observers.count(observer) == 0:
            self.observers.append(observer)

    def remove_observer(self, observer):
        if self.observers.count(observer) == 1:
            self.observers.remove(observer)

    def set_interface(self, interface):
        self.reset_interface()

        os.system("ip link set %s down" % interface)
        os.system("iw dev %s set type managed" % interface)
        os.system("ip link set %s up" % interface)

        self.interface = interface
        for observer in self.observers:
            observer.on_interface_up(self.interface)

    def reset_interface(self):
        if (self.interface is not None):
            for observer in self.observers:
                observer.on_interface_down(self.interface)

            self.interface = None

airshark_interface_manager = AirsharkInterfaceManager()


def configure(update):
    """
    Configure an Airshark interface.
    """
    hostConfig = update.cache_get('hostConfig')
    networkDevices = update.cache_get('networkDevices')

    interfaces = hostConfig.get('wifi-interfaces', [])
    airshark_interfaces = []

    # Look for objects in wifi-interfaces with mode == 'airshark'.
    for interface in interfaces:
        if interface.get('mode', None) != 'airshark':
            continue

        device = devices.resolveWirelessDevRef(interface['device'],
                networkDevices)
        if device['primary_interface'] is not None:
            airshark_interfaces.append(device['primary_interface'])

    if len(airshark_interfaces) > 1:
        raise Exception("Only one wifi interface can be in airshark mode")
    elif len(airshark_interfaces) == 1:
        airshark_interface = airshark_interfaces[0]
        airshark_interface_manager.set_interface(airshark_interface)
    else:
        airshark_interface_manager.reset_interface()
