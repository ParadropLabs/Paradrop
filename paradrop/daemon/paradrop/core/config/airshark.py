import os

from paradrop.core.config import devices

wifi_interface = None

def configure(update):
    hostConfig = update.new.getCache('hostConfig')
    networkDevices = update.new.getCache('networkDevices')

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
        global wifi_interface
        wifi_interface = airshark_interfaces[0]
        os.system("ip link set %s down" % wifi_interface)
        os.system("iw dev %s set type managed" % wifi_interface)
        os.system("ip link set %s up" % wifi_interface)
