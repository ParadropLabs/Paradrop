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
import subprocess
import yaml

from paradrop.base.output import out
from paradrop.base import settings
from paradrop.lib.config import devices as config_devices
from paradrop.lib.utils import datastruct

CHANNELS = [1, 6, 11]

def save(config, path=None):
    """
    Save host configuration.

    May raise exception if unable to write the configuration file.
    """
    if path is None:
        path = settings.HOST_CONFIG_FILE

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
        path = settings.HOST_CONFIG_FILE

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

    config['firewall'] = {
        'defaults': {
            'input': 'ACCEPT',
            'output': 'ACCEPT',
            'forward': 'ACCEPT'
        }
    }
    config['lan'] = {
        'interfaces': list(),
        'proto': 'static',
        'ipaddr': '192.168.1.1',
        'netmask': '255.255.255.0',
        'dhcp': {
            'start': 100,
            'limit': 100,
            'leasetime': '12h'
        },
        'firewall': {
            'defaults': {
                'conntrack': '1',
                'input': 'ACCEPT',
                'output': 'ACCEPT',
                'forward': 'ACCEPT'
            },
            'forwarding': []
        }
    }
    config['wifi'] = list()
    config['wifi-interfaces'] = list()
    config['system'] = {
        'autoUpdate': True,
        'onMissingWiFi': None
    }
    config['zerotier'] = {
        'enabled': False,
        'networks': []
    }

    # Cycle through the channel list to assign different channels to
    # WiFi interfaces.
    channels = itertools.cycle(CHANNELS)

    if len(devices['wan']) > 0:
        wanDev = devices['wan'][0]
        config['wan'] = {
            'interface': wanDev['name'],
            'proto': 'dhcp',
            'firewall': {
                'defaults': {
                    'conntrack': '1',
                    'masq': '1',
                    'input': 'ACCEPT',
                    'output': 'ACCEPT',
                    'forward': 'ACCEPT'
                }
            }
        }

        # Add a rule that forwards LAN traffic to WAN.
        config['lan']['firewall']['forwarding'].append({
            'src': 'lan',
            'dest': 'wan'
        })

    for lanDev in devices['lan']:
        config['lan']['interfaces'].append(lanDev['name'])

    for wifiDev in devices['wifi']:
        config['wifi'].append({
            'macaddr': wifiDev['mac'],
            'channel': channels.next(),
            'hwmode': '11g',
            'htmode': 'NONE'
        })

    if len(config['wifi']) > 0:
        # If we detect WiFi devices now, configure the system to warn if they
        # are missing later.  Production systems should be configured with
        # "reboot".
        config['system']['onMissingWiFi'] = "warn"

        # Add a default WiFi AP for usability.
        config['wifi-interfaces'].append({
            'device': devices['wifi'][0]['mac'],
            'ssid': 'ParaDrop',
            'mode': 'ap',
            'network': 'lan',
            'ifname': 'hwlan0'
        })

    return config


def prepareHostConfig(devices=None, hostConfigPath=None, write=True):
    """
    Load an existing host configuration or generate one.

    Tries to load host configuration from persistent file.  If that does not
    work, it will try to automatically generate a working configuration.

    write: if True and host config was automatically generated, then write
    the new host config to a file.
    """
    config = load(hostConfigPath)
    if config is not None:
        return config

    if devices is None:
        devices = config_devices.detectSystemDevices()
    config = generateHostConfig(devices)

    if write:
        save(config)

    return config


#
# Chute update operations
#


def getHostConfig(update):
    """
    Load host configuration.

    Read device information from networkDevices.
    Store host configuration in hostConfig.
    """
    # TODO We need to check for changes in hardware.  If a new device was
    # added, we should try to automatically configure it.  If a device was
    # removed, we should be aware of what is no longer valid.
    devices = update.new.getCache('networkDevices')
    config = prepareHostConfig(devices)

    # update.old is not guaranteed to contain the old host configuration, so
    # save a backup copy in update.new.  This will be used by revertHostConfig
    # if we need to back out.
    update.new.setCache('oldHostConfig', config)

    # If this is a sethostconfig operation, then read the host config from the
    # update object.  Ordinary chute operations should not alter the host
    # configuration.
    if update.updateType == 'sethostconfig':
        config = update.hostconfig

    # For factoryreset, try to load the default configuration or automatically
    # generate a new one if the file is not found.
    elif update.updateType == 'factoryreset':
        config = prepareHostConfig(devices,
                hostConfigPath=settings.DEFAULT_HOST_CONFIG_FILE)

    update.new.setCache('hostConfig', config)


def setAutoUpdate(enable):
    if enable:
        actions = ["enable", "start"]
    else:
        actions = ["disable", "stop"]

    for action in actions:
        cmd = ["systemctl", action, "snapd.refresh.timer"]
        subprocess.call(cmd)


def setHostConfig(update):
    """
    Write host configuration to persistent storage.

    Read host configuration from hostConfig.
    """
    config = update.new.getCache('hostConfig')
    setAutoUpdate(datastruct.getValue(config, "system.autoUpdate", True))
    save(config)


def revertHostConfig(update):
    """
    Restore host configuration from before update.

    Uses oldHostConfig cache entry.
    """
    config = update.new.getCache('oldHostConfig')
    setAutoUpdate(datastruct.getValue(config, "system.autoUpdate", True))
    save(config)
