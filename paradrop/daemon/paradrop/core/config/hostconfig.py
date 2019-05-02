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

import ipaddress
import jsonpatch
import yaml

from paradrop.base import settings
from paradrop.lib.utils import pdosq

from . import devices as config_devices

# This patch ensures the "unicode" function exists and behaves consistently
# between Python 2 and 3. Normally, it is recommended to use "builtins.str" for
# compatibility, but that uses a different class type not recognized by PyYAML.
try:
    unicode('')
except NameError:
    unicode = str


CHANNELS_24G = [1, 6, 11]
CHANNELS_5G  = [36, 40, 44, 48, 149, 153, 157, 161, 165]


WIFI_DEVICE_CAPS = {
    # WLE200NX
    ("0x168c", "0x002a"): {
        "hwmode": ["11a", "11g"]
    },

    # WLE600VX
    ("0x168c", "0x003c"): {
        "hwmode": ["11a", "11g"]
    },

    "default": {
        "hwmode": ["11g"]
    }
}

WIFI_DEVICE_PROFILE = {
    # WLE200NX
    ("0x168c", "0x002a"): {
        "htmode": "HT20",
        "tx_stbc": 1,
        "rx_stbc": 1,
        "short_gi_40": True,
    },

    # WLE600VX
    ("0x168c", "0x003c"): {
        "htmode": "VHT20",
        "tx_stbc": 1,
        "rx_stbc": 1,
        "short_gi_20": True,
        "short_gi_40": True,
        "short_gi_80": True
    },

    "default": {}
}


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

    return pdosq.read_yaml_file(path, default=None)


def generateHostConfig(devices):
    """
    Scan for devices on the machine and generate a working configuration.
    """
    config = dict()

    default_lan_network = ipaddress.ip_network(unicode(settings.DEFAULT_LAN_NETWORK))

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
        'ipaddr': settings.DEFAULT_LAN_ADDRESS,
        'netmask': unicode(default_lan_network.netmask),
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
        'chuteSubnetPool': settings.DYNAMIC_NETWORK_POOL,
        'chutePrefixSize': 24,
        'onMissingWiFi': None
    }
    config['telemetry'] = {
        'enabled': True,
        'interval': 60
    }
    config['zerotier'] = {
        'enabled': True,
        'networks': []
    }

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
                    'forward': 'ACCEPT',
                    'masq_src': [
                        settings.DEFAULT_LAN_NETWORK,
                        settings.DYNAMIC_NETWORK_POOL
                    ]
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

    # Counters to help with channel assignment.
    serial = config_devices.get_hardware_serial()
    wifi_24_assigned = 0
    wifi_5_assigned = 0

    for wifiDev in devices['wifi']:
        pair = (wifiDev['vendor'], wifiDev['device'])
        if pair in WIFI_DEVICE_PROFILE:
            new_config = WIFI_DEVICE_PROFILE[pair].copy()
            wifi_caps = WIFI_DEVICE_CAPS[pair]
        else:
            new_config = WIFI_DEVICE_PROFILE['default'].copy()
            wifi_caps = WIFI_DEVICE_CAPS["default"]

        new_config['id'] = wifiDev['id']

        # This logic will assign a 5 Ghz channel to the first 5 Ghz-capable
        # device.  It will then alternate between 2.4 Ghz and 5 Ghz.
        choose_5g = "11a" in wifi_caps.get('hwmode', []) and \
                wifi_5_assigned <= wifi_24_assigned

        if choose_5g:
            chan_index = (serial + wifi_5_assigned) % len(CHANNELS_5G)
            new_config['channel'] = CHANNELS_5G[chan_index]
            new_config['hwmode'] = "11a"
            wifi_5_assigned += 1
        else:
            chan_index = (serial + wifi_24_assigned) % len(CHANNELS_24G)
            new_config['channel'] = CHANNELS_24G[chan_index]
            new_config['hwmode'] = "11g"
            wifi_24_assigned += 1

        config['wifi'].append(new_config)

    if len(config['wifi']) > 0 and settings.DEFAULT_WIRELESS_ENABLED:
        # If we detect WiFi devices now, configure the system to warn if they
        # are missing later.  Production systems should be configured with
        # "reboot".
        config['system']['onMissingWiFi'] = "warn"

        # Add a default WiFi AP for usability.
        new_iface = {
            'device': devices['wifi'][0]['id'],
            'ssid': settings.DEFAULT_WIRELESS_ESSID,
            'mode': 'ap',
            'network': 'lan'
        }

        if settings.DEFAULT_WIRELESS_KEY:
            new_iface['encryption'] = "psk2"
            new_iface['key'] = settings.DEFAULT_WIRELESS_KEY

        config['wifi-interfaces'].append(new_iface)

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
    devices = update.cache_get('networkDevices')
    config = prepareHostConfig(devices)

    # update.old is not guaranteed to contain the old host configuration, so
    # save a backup copy in update.new.  This will be used by revertHostConfig
    # if we need to back out.
    update.cache_set('oldHostConfig', config)

    # If this is a sethostconfig operation, then read the host config from the
    # update object.  Ordinary chute operations should not alter the host
    # configuration.
    if update.updateType == 'sethostconfig':
        config = update.hostconfig

    elif update.updateType == 'patchhostconfig':
        config = jsonpatch.apply_patch(config, update.patch)

    # For factoryreset, try to load the default configuration or automatically
    # generate a new one if the file is not found.
    elif update.updateType == 'factoryreset':
        config = prepareHostConfig(devices,
                hostConfigPath=settings.DEFAULT_HOST_CONFIG_FILE)

    update.cache_set('hostConfig', config)


def setHostConfig(update):
    """
    Write host configuration to persistent storage.

    Read host configuration from hostConfig.
    """
    config = update.cache_get('hostConfig')
    save(config)


def revertHostConfig(update):
    """
    Restore host configuration from before update.

    Uses oldHostConfig cache entry.
    """
    config = update.cache_get('oldHostConfig')
    save(config)
