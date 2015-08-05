
from paradrop.lib.config import configservice, uciutils
from paradrop.lib.utils import uci
from pdtools.lib.output import out


def getOSWirelessConfig(update):
    # old code under lib.internal.chs.chutelxc same function name
    # Basically the same as the networking version of this

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
            'mode': 'ap',
            'ssid': iface['ssid']
        }

        # Optional encryption settings
        if 'encryption' in iface:
            options['encryption'] = iface['encryption']
        if 'key' in iface:
            options['key'] = iface['key']

        wifiIfaces.append((config, options))

    update.new.setCache('osWirelessConfig', wifiIfaces)


def setOSWirelessConfig(update):
    # Basically the same as the networking version of this

    changed = uciutils.setConfig(update.new, update.old,
                                 cacheKeys=['osWirelessConfig'],
                                 filepath=uci.getSystemPath("wireless"))
