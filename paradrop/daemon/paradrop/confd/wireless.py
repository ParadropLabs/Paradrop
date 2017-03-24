import heapq
import ipaddress
import os
import random
import string
import subprocess
from pprint import pprint

from paradrop.base.output import out
from paradrop.lib.utils import pdosq

from .base import ConfigObject, ConfigOption
from .command import Command, KillCommand


IEEE80211_DIR = "/sys/class/ieee80211"


# Map hardware mode strings from UCI file to hostapd.conf format.
HOSTAPD_HWMODE = {
    '11b': 'b',
    '11g': 'g',
    '11a': 'a'
}


# Map wifi-iface mode values to the type string we pass when running iw
# commands.
IW_IFACE_TYPE = {
    'ap': '__ap',
    'monitor': 'monitor',
    'sta': 'managed'
}


HT40_LOWER_CHANNELS = set([36, 44, 52, 60, 100, 108, 116, 124, 132, 140, 149, 157])
HT40_UPPER_CHANNELS = set([40, 48, 56, 64, 104, 112, 120, 128, 136, 144, 153, 161])

# Map 20 Mhz channel to index of 40 Mhz channel that contains it.
VHT40_CENTER_INDEX = {
    36: 38,
    40: 38,
    44: 46,
    48: 46,
    52: 54,
    56: 54,
    60: 62,
    64: 62,
    100: 102,
    104: 102,
    108: 110,
    112: 110,
    116: 118,
    120: 118,
    124: 126,
    128: 126,
    132: 134,
    136: 134,
    140: 142,
    144: 142,
    149: 151,
    153: 151,
    157: 159,
    161: 159
}

# Map 20 Mhz channel to index of 80 Mhz channel that contains it.
VHT80_CENTER_INDEX = {
    36: 42,
    40: 42,
    44: 42,
    48: 42,
    52: 58,
    56: 58,
    60: 58,
    64: 58,
    100: 106,
    104: 106,
    108: 106,
    112: 106,
    116: 122,
    120: 122,
    124: 122,
    128: 122,
    132: 138,
    136: 138,
    140: 138,
    144: 138,
    149: 155,
    153: 155,
    157: 155,
    161: 155
}

# Map 20 Mhz channel to index of 160 Mhz channel that contains it.
VHT160_CENTER_INDEX = {
    36: 50,
    40: 50,
    44: 50,
    48: 50,
    52: 50,
    56: 50,
    60: 50,
    64: 50,
    100: 114,
    104: 114,
    108: 114,
    112: 114,
    116: 114,
    120: 114,
    124: 114,
    128: 114
}


def getPhyMACAddress(phy):
    path = "{}/{}/macaddress".format(IEEE80211_DIR, phy)
    with open(path, 'r') as source:
        return source.read().strip()


def getPhyFromMAC(mac):
    for phy in os.listdir(IEEE80211_DIR):
        if getPhyMACAddress(phy) == mac:
            return phy
    raise Exception("No wireless device with MAC address {}".format(mac))


def isHexString(data):
    """
    Test if a string contains only hex digits.
    """
    return all(c in string.hexdigits for c in data)


class ConfigWifiDevice(ConfigObject):
    typename = "wifi-device"

    options = [
        ConfigOption(name="type", required=True),
        ConfigOption(name="phy", type=str),
        ConfigOption(name="macaddr", type=str),
        ConfigOption(name="ifname", type=str),
        ConfigOption(name="channel", type=int, required=True),
        ConfigOption(name="hwmode"),
        ConfigOption(name="txpower", type=int),
        ConfigOption(name="country"),
        ConfigOption(name="require_mode"),
        ConfigOption(name="htmode"),
        ConfigOption(name="beacon_int", type=int),
        ConfigOption(name="frag", type=int),
        ConfigOption(name="rts", type=int),

        # 802.11n Capabilities
        ConfigOption(name="short_gi_20", type=bool),
        ConfigOption(name="short_gi_40", type=bool),
        ConfigOption(name="tx_stbc", type=int),
        ConfigOption(name="rx_stbc", type=int),
        ConfigOption(name="dsss_cck_40", type=bool),

        # 802.11ac Capabilities
        ConfigOption(name="short_gi_80", type=bool),
        ConfigOption(name="short_gi_160", type=bool),
        ConfigOption(name="tx_stbc_2by1", type=bool),
        ConfigOption(name="rx_antenna_pattern", type=bool),
        ConfigOption(name="tx_antenna_pattern", type=bool),
        ConfigOption(name="rx_stbc", type=int)
    ]

    def setup(self):
        self._phy = self.phy
        if self._phy is None and self.macaddr is not None:
            self._phy = getPhyFromMAC(self.macaddr)

    def apply(self, allConfigs):
        commands = []

        if self.txpower is not None:
            # txpower is in dBm, iw takes mBm.
            power = self.txpower * 100
            cmd = ["iw", "phy", self._phy, "set", "txpower",
                    "fixed", str(power)]
        else:
            cmd = ["iw", "phy", self._phy, "set", "txpower", "auto"]

        commands.append((self.PRIO_CONFIG_IFACE, Command(cmd, self)))
        return commands

    def revert(self, allConfigs):
        commands = []

        # We only need to revert txpower if it was actually set in the apply
        # step.
        if self.txpower is not None:
            cmd = ["iw", "phy", self._phy, "set", "txpower", "auto"]
            commands.append((-self.PRIO_CONFIG_IFACE, Command(cmd, self)))

        return commands


class ConfigWifiIface(ConfigObject):
    typename = "wifi-iface"

    options = [
        ConfigOption(name="device", required=True),
        ConfigOption(name="mode", required=True),
        ConfigOption(name="ssid", default="Paradrop"),
        ConfigOption(name="hidden", type=bool, default=False),
        ConfigOption(name="wmm", type=bool, default=True),
        ConfigOption(name="network", default="lan"),
        ConfigOption(name="encryption", default="none"),
        ConfigOption(name="key"),
        ConfigOption(name="maxassoc", type=int),

        ConfigOption(name="doth", type=bool, default=True),
        ConfigOption(name="short_preamble", type=bool, default=True),

        # WPA Enterprise (RADIUS) options
        ConfigOption(name="auth_server"),
        ConfigOption(name="auth_port", type=int, default=1812),
        ConfigOption(name="auth_secret"),
        ConfigOption(name="acct_server"),
        ConfigOption(name="acct_port", type=int, default=1813),
        ConfigOption(name="acct_secret"),
        ConfigOption(name="nasid"),
        ConfigOption(name="ownip"),
        ConfigOption(name="dynamic_vlan", type=int, default=0),

        # WPA Enterprise (Client)
        ConfigOption(name="identity"),
        ConfigOption(name="password"),

        # Nonstandard: interval (seconds) for sending interim updates.
        ConfigOption(name="acct_interval", type=int, default=300),

        # NOTE: ifname is not defined in the UCI specs.  We use it to declare a
        # desired name for the virtual wireless interface that should be
        # created.
        ConfigOption(name="ifname")
    ]

    def getIfname(self, interface=None, allConfigs=None):
        """
        Returns the name to be used by this WiFi interface, e.g. as seen by
        ifconfig.

        This comes from the "ifname" option if it is set.  Otherwise, we use
        the interface name of the associated network.

        Either interface or allConfigs must be set.
        """
        if self.ifname is not None:
            return self.ifname
        elif interface is not None:
            return interface.config_ifname
        else:
            interface = self.lookup(allConfigs, "network", "interface", self.network)
            return interface.config_ifname

    def getName(self):
        if self.ifname is None:
            return ConfigObject.getName(self)
        else:
            return self.ifname

    def apply(self, allConfigs):
        commands = list()

        # Look up the wifi-device section.
        wifiDevice = self.lookup(allConfigs, "wireless", "wifi-device", self.device)

        # Look up the interface section.
        interface = self.lookup(allConfigs, "network", "interface", self.network)

        # Type to pass to iw command, e.g. '__ap'.
        iw_type = IW_IFACE_TYPE[self.mode]

        # Set _ifname while the section is being applied so that it is still
        # available when the section is being reverted.
        self._ifname = self.getIfname(interface=interface)

        # Try removing interface first in case it already exists.
        cmd = ["iw", "dev", self._ifname, "del"]
        commands.append((self.PRIO_CREATE_IFACE, Command(cmd, self, ignoreFailure=True)))

        # Command to create the virtual interface.
        cmd = ["iw", "phy", wifiDevice._phy, "interface", "add",
               self._ifname, "type", iw_type]
        commands.append((self.PRIO_CREATE_IFACE, Command(cmd, self)))

        # Assign a random MAC address to avoid conflict with other
        # interfaces using the same device.
        cmd = ["ip", "link", "set", "dev", self._ifname,
                "address", self.getRandomMAC()]
        commands.append((self.PRIO_CREATE_IFACE, Command(cmd, self)))

        if self.mode == "ap":
            confFile = self.makeHostapdConf(wifiDevice, interface)

            self.pidFile = "{}/hostapd-{}.pid".format(
                self.manager.writeDir, self.internalName)

            cmd = ["hostapd", "-P", self.pidFile, "-B", confFile]
            commands.append((self.PRIO_START_DAEMON, Command(cmd, self)))

        elif self.mode == "sta":
            confFile = self.makeWpaSupplicantConf(wifiDevice, interface)

            self.pidFile = "{}/wpa_supplicant-{}.pid".format(
                self.manager.writeDir, self.internalName)

            cmd = ["wpa_supplicant", "-B", "-c", confFile, "-i", self._ifname,
                    "-D", "nl80211", "-P", self.pidFile]
            commands.append((self.PRIO_START_DAEMON, Command(cmd, self)))

        return commands

    def makeHostapdConf(self, wifiDevice, interface):
        outputPath = "{}/hostapd-{}.conf".format(
            self.manager.writeDir, self.internalName)

        conf = HostapdConfGenerator(self, wifiDevice, interface)
        conf.generate(outputPath)

        return outputPath

    def makeWpaSupplicantConf(self, wifiDevice, interface):
        outputPath = "{}/wpa_supplicant-{}.conf".format(
            self.manager.writeDir, self.internalName)

        conf = WpaSupplicantConfGenerator(self, wifiDevice, interface)
        conf.generate(outputPath)

        return outputPath

    def revert(self, allConfigs):
        commands = list()

        if self.mode == "ap":
            commands.append((-self.PRIO_START_DAEMON,
                KillCommand(self.pidFile, self)))

        # Delete our virtual interface.
        cmd = ["iw", "dev", self._ifname, "del"]
        commands.append((-self.PRIO_CREATE_IFACE, Command(cmd, self, ignoreFailure=True)))

        return commands

    def updateApply(self, new, allConfigs):
        if new.mode != self.mode or \
                new.device != self.device or \
                new.network != self.network:
            # Major change requires unloading the old section and applying the
            # new.
            return self.apply(allConfigs)

        commands = list()

        if new.mode == "ap":
            # Look up the wifi-device section.
            wifiDevice = new.lookup(allConfigs, "wireless", "wifi-device", new.device)

            # Look up the interface section.
            interface = new.lookup(allConfigs, "network", "interface", new.network)

            confFile = new.makeHostapdConf(wifiDevice, interface)

            new.pidFile = "{}/hostapd-{}.pid".format(
                new.manager.writeDir, new.internalName)

            cmd = ["hostapd", "-P", new.pidFile, "-B", confFile]
            commands.append((self.PRIO_START_DAEMON, Command(cmd, new)))

        return commands

    def updateRevert(self, new, allConfigs):
        if new.mode != self.mode or \
                new.device != self.device or \
                new.network != self.network:
            # Major change requires unloading the old section and applying the
            # new.
            return self.revert(allConfigs)

        commands = list()

        if self.mode == "ap":
            # Bring down hostapd
            commands.append((-self.PRIO_START_DAEMON,
                KillCommand(self.pidFile, self)))

        return commands

    def getRandomMAC(self):
        """
        Generate a random MAC address.

        Returns a string "02:xx:xx:xx:xx:xx".  The first byte is 02, which
        indicates a locally administered address.
        """
        parts = ["02"]
        for i in range(5):
            parts.append("{:02x}".format(random.randrange(0, 255)))
        return ":".join(parts)


class ConfGenerator(object):
    def writeHeader(self, output):
        output.write("#" * 79 + "\n")
        output.write("# Configuration file generated by pdconf\n")
        output.write("#" * 79 + "\n")

    def writeOptions(self, options, output, title=None):
        output.write("\n")
        if title is not None:
            head = "##### {} ".format(title)
            tail = "#" * (79 - len(head))
            output.write(head + tail + "\n")
        for name, value in options:
            if isinstance(value, list):
                output.write("{}={{\n".format(name))
                for subname, subvalue, quote in value:
                    if quote:
                        output.write("\t{}=\"{}\"\n".format(subname, subvalue))
                    else:
                        output.write("\t{}={}\n".format(subname, subvalue))
                output.write("}\n")
            else:
                output.write("{}={}\n".format(name, value))


class HostapdConfGenerator(ConfGenerator):
    def __init__(self, wifiIface, wifiDevice, interface):
        self.wifiIface = wifiIface
        self.wifiDevice = wifiDevice
        self.interface = interface

        self.readMode(wifiDevice)

    def readMode(self, device):
        """
        Determine HT/VHT mode if applicable.
        """
        self.enable11n = False
        self.enable11ac = False

        if device.htmode is None:
            return

        if device.htmode.startswith("HT"):
            self.enable11n = True
        elif device.htmode.startswith("VHT"):
            self.enable11n = True
            self.enable11ac = True

    def generate(self, path):
        with open(path, "w") as output:
            self.writeHeader(output)

            options = self.getMainOptions()
            self.writeOptions(options, output)

            if self.enable11n:
                options = self.get11nOptions()
                self.writeOptions(options, output, title="802.11n")

            if self.enable11ac:
                options = self.get11acOptions()
                self.writeOptions(options, output, title="802.11ac")

            options = self.getSecurityOptions()
            self.writeOptions(options, output, title="Security")

            options = self.getRadiusOptions()
            if len(options) > 0:
                self.writeOptions(options, output, title="RADIUS Client")

    def getMainOptions(self):
        options = list()

        ifname = self.wifiIface.getIfname(interface=self.interface)
        options.append(("interface", ifname))

        if self.interface.type == "bridge":
            options.append(("bridge", self.interface.config_ifname))

        options.append(("ssid", self.wifiIface.ssid))

        if self.wifiDevice.country is not None:
            options.append(("country_code", self.wifiDevice.country))
            options.append(("ieee80211d", 1))
            if self.wifiIface.doth:
                options.append(("ieee80211h", 1))

        hwmode = self.wifiDevice.hwmode
        if hwmode is not None:
            if hwmode in HOSTAPD_HWMODE:
                # Convert UCI hwmode to hostapd hwmode format.
                options.append(("hw_mode", HOSTAPD_HWMODE[hwmode]))
            else:
                raise Exception("Unrecognized hardware mode: {}".format(hwmode))

        options.append(("channel", self.wifiDevice.channel))

        if self.wifiDevice.beacon_int is not None:
            options.append(("beacon_int", self.wifiDevice.beacon_int))

        if self.wifiIface.maxassoc is not None:
            options.append(("max_num_sta", self.wifiIface.maxassoc))

        if self.wifiDevice.rts is not None:
            options.append(("rts_threshold", self.wifiDevice.rts))
        if self.wifiDevice.frag is not None:
            options.append(("fragm_threshold", self.wifiDevice.rts))

        if self.wifiIface.short_preamble:
            options.append(("preamble", 1))

        options.append(("wmm_enabled", 1 * self.wifiIface.wmm))

        return options

    def get11nOptions(self):
        options = list()

        options.append(("ieee80211n", 1 * self.enable11n))

        ht_capab = ""
        if self.wifiDevice.htmode.startswith("HT40"):
            ht_capab += "[{}]".format(self.wifiDevice.htmode)
        elif self.wifiDevice.htmode in ["VHT40", "VHT80", "VHT160"]:
            if self.wifiDevice.channel in HT40_LOWER_CHANNELS:
                ht_capab += "[HT40+]"
            elif self.wifiDevice.channel in HT40_UPPER_CHANNELS:
                ht_capab += "[HT40-]"

        if self.wifiDevice.short_gi_20:
            ht_capab += "[SHORT-GI-20]"
        if self.wifiDevice.short_gi_40:
            ht_capab += "[SHORT-GI-40]"
        if self.wifiDevice.tx_stbc:
            ht_capab += "[TX-STBC]"
        if self.wifiDevice.rx_stbc == 1:
            ht_capab += "[RX-STBC1]"
        elif self.wifiDevice.rx_stbc == 2:
            ht_capab += "[RX-STBC12]"
        elif self.wifiDevice.rx_stbc >= 3:
            ht_capab += "[RX-STBC123]"
        if self.wifiDevice.dsss_cck_40:
            ht_capab += "[DSSS_CCK-40]"

        if len(ht_capab) > 0:
            options.append(("ht_capab", ht_capab))

        if self.wifiDevice.require_mode == "n":
            options.append(("require_ht", 1))

        return options

    def get11acOptions(self):
        options = list()

        options.append(("ieee80211ac", 1 * self.enable11ac))

        if self.wifiDevice.require_mode == "ac":
            options.append(("require_vht", 1))

        # Default chwidth=0 means 20 or 40 Mhz.
        chwidth = 0
        seg0_idx = self.wifiDevice.channel
        seg1_idx = None
        if self.wifiDevice.htmode == "VHT40":
            seg0_idx = VHT40_CENTER_INDEX[self.wifiDevice.channel]
        elif self.wifiDevice.htmode == "VHT80":
            chwidth = 1
            seg0_idx = VHT80_CENTER_INDEX[self.wifiDevice.channel]
        elif self.wifiDevice.htmode == "VHT160":
            chwidth = 2
            seg0_idx = VHT160_CENTER_INDEX[self.wifiDevice.channel]
        # TODO: How does the admin request 80+80 mode (chwidth=3)?
        # We need a second channel number to specify seg1_idx in that case.

        vht_capab = ""
        if self.wifiDevice.short_gi_80:
            vht_capab += "[SHORT-GI-80]"
        if self.wifiDevice.short_gi_160:
            vht_capab += "[SHORT-GI-160]"
        if self.wifiDevice.tx_stbc_2by1:
            vht_capab += "[TX-STBC-2BY1]"
        if self.wifiDevice.rx_antenna_pattern:
            vht_capab += "[RX-ANTENNA-PATTERN]"
        if self.wifiDevice.tx_antenna_pattern:
            vht_capab += "[TX-ANTENNA-PATTERN]"
        if self.wifiDevice.rx_stbc == 1:
            vht_capab += "[RX-STBC-1]"
        elif self.wifiDevice.rx_stbc == 2:
            vht_capab += "[RX-STBC-12]"
        elif self.wifiDevice.rx_stbc == 3:
            vht_capab += "[RX-STBC-123]"
        elif self.wifiDevice.rx_stbc >= 4:
            vht_capab += "[RX-STBC-1234]"
        if len(vht_capab) > 0:
            options.append(("vht_capab", vht_capab))

        options.append(("vht_oper_chwidth", chwidth))
        options.append(("vht_oper_centr_freq_seg0_idx", seg0_idx))
        if seg1_idx is not None:
            options.append(("vht_oper_centr_freq_seg1_idx", seg1_idx))

        return options

    def getSecurityOptions(self):
        options = list()

        if self.wifiIface.encryption is None or \
                self.wifiIface.encryption == "none":
            options.append(("wpa", 0))
            return options

        modes = self.wifiIface.encryption.split("+")
        if modes[0] == "psk2":
            options.append(("wpa", 1))

            # If key is a 64 character hex string, then treat it as the PSK
            # directly, else treat it as a passphrase.
            if len(self.wifiIface.key) == 64 and isHexString(self.wifiIface.key):
                options.append(("wpa_psk", self.wifiIface.key))
            else:
                options.append(("wpa_passphrase", self.wifiIface.key))

            options.append(("wpa_key_mgmt", "WPA-PSK"))

            # Encryption for WPA
            options.append(("wpa_pairwise", "TKIP CCMP"))

            # Encryption for WPA2
            options.append(("rsn_pairwise", "CCMP"))

        elif modes[0] == "wpa2":
            if self.wifiIface.auth_server is None:
                raise Exception("Must configure auth_server with wpa2")

            options.append(("wpa", 2))

            options.append(("wpa_key_mgmt", "WPA-EAP"))

            # Encryption for WPA
            options.append(("wpa_pairwise", "TKIP CCMP"))

            # Encryption for WPA2
            options.append(("rsn_pairwise", "CCMP"))

            # TODO: Separate section for 802.1X?
            options.append(("ieee8021x", "1"))

        else:
            out.warn("Encryption type {} not supported (supported: "
                     "none|psk2)".format(self.wifiIface.encryption))
            raise Exception("Encryption type not supported")

        return options

    def getRadiusOptions(self):
        options = list()

        if self.wifiIface.ownip:
            options.append(("own_ip_addr", self.wifiIface.ownip))
        if self.wifiIface.nasid:
            options.append(("nas_identifier", self.wifiIface.nasid))

        if self.wifiIface.auth_server:
            options.append(("auth_server_addr", self.wifiIface.auth_server))
            options.append(("auth_server_port", self.wifiIface.auth_port))
            if self.wifiIface.auth_secret:
                options.append(("auth_server_shared_secret",
                    self.wifiIface.auth_secret))
            options.append(("dynamic_vlan", self.wifiIface.dynamic_vlan))

        if self.wifiIface.acct_server:
            options.append(("acct_server_addr", self.wifiIface.acct_server))
            options.append(("acct_server_port", self.wifiIface.acct_port))
            if self.wifiIface.acct_secret:
                options.append(("acct_server_shared_secret",
                    self.wifiIface.acct_secret))
            options.append(("radius_acct_interim_interval", self.wifiIface.acct_interval))

        return options

    def writeHeader(self, output):
        output.write("#" * 79 + "\n")
        output.write("# hostapd configuration file generated by pdconf\n")
        output.write("# Source: {}\n".format(self.wifiIface.source))
        output.write("# Section: {}\n".format(str(self.wifiIface)))
        output.write("# Device: {}\n".format(str(self.wifiDevice)))
        output.write("# Interface: {}\n".format(str(self.interface)))
        output.write("#" * 79 + "\n")


class WpaSupplicantConfGenerator(ConfGenerator):
    def __init__(self, wifiIface, wifiDevice, interface):
        self.wifiIface = wifiIface
        self.wifiDevice = wifiDevice
        self.interface = interface

    def generate(self, path):
        with open(path, "w") as output:
            self.writeHeader(output)

            options = self.getMainOptions()
            self.writeOptions(options, output)

    def getMainOptions(self):
        options = list()

        options.append(("ap_scan", 1))
        if self.wifiDevice.country is not None:
            options.append(("country", self.wifiDevice.country))

        # (name, value, quote)
        network = list()

        network.append(('ssid', self.wifiIface.ssid, True))
        network.append(('scan_ssid', 1, False))

        modes = self.wifiIface.encryption.split("+")
        if modes[0] == "psk2":
            network.append(('key_mgmt', 'WPA-PSK', False))
            network.append(('psk', self.wifiIface.key, True))

        elif modes[0] == "wpa2":
            network.append(('key_mgmt', 'WPA-EAP', False))
            network.append(('identity', self.wifiIface.identity))
            network.append(('password', self.wifiIface.password))

        else:
            network.append(('key_mgmt', 'NONE', False))

        options.append(("network", network))

        return options

    def writeHeader(self, output):
        output.write("#" * 79 + "\n")
        output.write("# wpa_supplicant configuration file generated by pdconf\n")
        output.write("# Source: {}\n".format(self.wifiIface.source))
        output.write("# Section: {}\n".format(str(self.wifiIface)))
        output.write("# Device: {}\n".format(str(self.wifiDevice)))
        output.write("# Interface: {}\n".format(str(self.interface)))
        output.write("#" * 79 + "\n")
