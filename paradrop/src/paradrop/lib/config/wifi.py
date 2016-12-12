from paradrop.base.output import out
from paradrop.lib.config import configservice, uciutils
from paradrop.lib.utils import uci


def getOSWirelessConfig(update):
    """
    Read settings from networkInterfaces for wireless interfaces.
    Store wireless configuration settings in osWirelessConfig.
    """
    # old code under lib.internal.chs.chutelxc same function name

    interfaces = update.new.getCache('networkInterfaces')
    if interfaces is None:
        return

    wifiIfaces = list()
    for iface in interfaces:
        # Only look at wifi interfaces.
        if iface['netType'] != "wifi":
            continue

        config = {'type': 'wifi-iface'}
        options = {
            'device': iface['device'],
            'network': iface['externalIntf'],
            'mode': iface.get('mode', 'ap')
        }

        # Required for AP and client mode but not monitor mode.
        if 'ssid' in iface:
            options['ssid'] = iface['ssid']

        # Optional encryption settings
        if 'encryption' in iface:
            options['encryption'] = iface['encryption']
        if 'key' in iface:
            options['key'] = iface['key']

        wifiIfaces.append((config, options))

    update.new.setCache('osWirelessConfig', wifiIfaces)


def setOSWirelessConfig(update):
    """
    Write settings from osWirelessConfig out to UCI files.
    """
    changed = uciutils.setConfig(update.new, update.old,
                                 cacheKeys=['osWirelessConfig'],
                                 filepath=uci.getSystemPath("wireless"))
