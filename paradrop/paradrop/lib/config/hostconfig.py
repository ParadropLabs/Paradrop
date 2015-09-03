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
from paradrop.lib.config import devices as config_devices


SYS_DIR = "/sys/class/net"
EXCLUDE_IFACES = set(["lo"])
CHANNELS = [1, 6, 11]

# Strings that identify a virtual interface.
VIF_MARKERS = [".", "veth"]


def save(config, path=None):
    """
    Save host configuration.

    May raise exception if unable to write the configuration file.
    """
    if path is None:
        path = settings.HOST_CONFIG_PATH

    with open(path, 'w') as output:
        output.write(yaml.safe_dump(config, default_flow_style=False))


def load(path=None):
    """
    Load host configuration.

    Tries to load host configuration from persistent file.  If that does not
    work, it will try to automatically generate a working configuration.

    Returns a host config object on success or None on failure.
    """
    if path is None:
        path = settings.HOST_CONFIG_PATH

    try:
        with open(path, 'r') as source:
            data = yaml.safe_load(source.read())
            return data
    except IOError as e:
        pass

    return None


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


def prepareHostConfig(devices=None, hostConfigPath=None):
    """
    Load an existing host configuration or generate one.

    Tries to load host configuration from persistent file.  If that does not
    work, it will try to automatically generate a working configuration.
    """
    config = load(hostConfigPath)
    if config is not None:
        return config

    if devices is None:
        devices = config_devices.detectSystemDevices()
    config = generateHostConfig(devices)

    save(config)

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
    config = prepareHostConfig(devices)
    update.new.setCache('hostConfig', config)
