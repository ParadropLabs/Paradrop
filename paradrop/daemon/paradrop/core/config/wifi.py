from paradrop.lib.utils import uci

from . import uciutils


def getOSWirelessConfig(update):
    """
    Read settings from networkInterfaces for wireless interfaces.
    Store wireless configuration settings in osWirelessConfig.
    """
    # old code under lib.internal.chs.chutelxc same function name

    interfaces = update.cache_get('networkInterfaces')
    if interfaces is None:
        return

    wifiIfaces = list()
    for iface in interfaces:
        # Only look at wifi interfaces.
        if not iface['type'].startswith("wifi"):
            continue

        config = {'type': 'wifi-iface'}
        options = {
            'device': iface['device'],
            'network': iface['externalIntf'],
            'mode': iface.get('mode', 'ap')
        }

        # Add wireless options.
        options.update(iface['wireless'])

        # Required for AP and client mode but not monitor mode.
        if 'ssid' in iface:
            options['ssid'] = iface['ssid']

        # Optional encryption settings
        if 'encryption' in iface:
            options['encryption'] = iface['encryption']
        if 'key' in iface:
            options['key'] = iface['key']

        wifiIfaces.append((config, options))

    update.cache_set('osWirelessConfig', wifiIfaces)


def setOSWirelessConfig(update):
    """
    Write settings from osWirelessConfig out to UCI files.
    """
    uciutils.setConfig(update,
            cacheKeys=['osWirelessConfig'],
            filepath=uci.getSystemPath("wireless"))


def revert_os_wireless_config(update):
    uciutils.setConfig(update,
            cacheKeys=['osWirelessConfig'],
            filepath=uci.getSystemPath("wireless"))
