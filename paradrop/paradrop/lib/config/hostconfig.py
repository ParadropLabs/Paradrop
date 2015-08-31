"""
The host configuration controls system settings of the host OS.

This module operates as follows:

1. The first time, we try to detect all devices and auto-generate
a reasonable configuration, which we store to a persistent file.

2. (TODO) We present the configuration to the owner sometime around
provisioning or first chute creation and allow him to change settings.

3. (TODO) We have some kind of update operation that can manipulate
settings.
"""

import itertools
import os
import re
import yaml

from pdtools.lib.output import out
from paradrop.lib import settings


SYS_DIR = "/sys/class/net"
EXCLUDE_IFACES = set(["lo"])
CHANNELS = [1, 6, 11]

# Strings that identify a virtual interface.
VIF_MARKERS = [".", "veth"]


def generateHostConfig(devices):
    """
    Scan for devices on the machine and generate a working configuration.
    """
    config = dict()

    config['lan'] = {
        'interfaces': list(),
        'proto': 'static',
        'ipaddr': '192.168.1.1',
        'netmask': '255.255.255.0',
        'dhcp': {
            'start': 100,
            'limit': 100,
            'leasetime': '12h'
        }
    }
    config['wifi'] = list()

    # Cycle through the channel list to assign different channels to
    # WiFi interfaces.
    channels = itertools.cycle(CHANNELS)

    if len(devices['wan']) > 0:
        wanDev = devices['wan'][0]
        config['wan'] = {
            'interface': wanDev['name'],
            'proto': 'dhcp'
        }

    for lanDev in devices['lan']:
        config['lan']['interfaces'].append(lanDev['name'])

    for wifiDev in devices['wifi']:
        newWifi = {
            'interface': wifiDev['name'],
            'channel': channels.next()
        }

        config['wifi'].append(newWifi)

    return config


def loadHostConfig(devices, hostConfigPath=None):
    """
    Load host configuration.

    Tries to load host configuration from persistent file.  If that does not
    work, it will try to automatically generate a working configuration.
    """
    path = settings.HOST_CONFIG_PATH

    try:
        with open(path, 'r') as source:
            config = yaml.load(source.read())
            return config
    except IOError as e:
        pass

    config = generateHostConfig(devices)

    try:
        with open(path, 'w') as output:
            output.write(yaml.dump(config, default_flow_style=False))
    except IOError as e:
        out.exception(e, True)

    return config


#
# Chute update operations
#


def getHostConfig(update):
    """
    Load host configuration.
    """
    # TODO We need to check for changes in hardware.  If a new device was
    # added, we should try to automatically configure it.  If a device was
    # removed, we should be aware of what is no longer valid.
    devices = update.new.getCache('networkDevices')
    config = loadHostConfig(devices)
    update.new.setCache('hostConfig', config)
