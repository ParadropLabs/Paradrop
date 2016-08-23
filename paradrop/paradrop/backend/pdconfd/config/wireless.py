import heapq
import ipaddress
import os
import random
import string
import subprocess
from pprint import pprint

from pdtools.lib.output import out
from paradrop.lib.utils import pdosq

from .base import ConfigObject, ConfigOption
from .command import Command, KillCommand


# Map hardware mode strings from UCI file to hostapd.conf format.
HOSTAPD_HWMODE = {
    '11b': 'b',
    '11g': 'g',
    '11a': 'a'
}


def isHexString(data):
    """
    Test if a string contains only hex digits.
    """
    return all(c in string.hexdigits for c in data)


class ConfigWifiDevice(ConfigObject):
    typename = "wifi-device"

    options = [
        ConfigOption(name="type", required=True),
        ConfigOption(name="channel", type=int, required=True),
        ConfigOption(name="hwmode"),
        ConfigOption(name="txpower", type=int),
        ConfigOption(name="country"),
        ConfigOption(name="require_mode"),
        ConfigOption(name="htmode"),
        ConfigOption(name="beacon_int", type=int),
        ConfigOption(name="frag", type=int),
        ConfigOption(name="rts", type=int)
    ]


class ConfigWifiIface(ConfigObject):
    typename = "wifi-iface"

    options = [
        ConfigOption(name="device", required=True),
        ConfigOption(name="mode", required=True),
        ConfigOption(name="ssid", required=True),
        ConfigOption(name="hidden", type=bool, default=False),
        ConfigOption(name="network", required=True),
        ConfigOption(name="encryption"),
        ConfigOption(name="key"),
        ConfigOption(name="maxassoc", type=int),

        # NOTE: ifname is not defined in the UCI specs.  We use it to declare a
        # desired name for the virtual wireless interface that should be
        # created.
        ConfigOption(name="ifname")
    ]

    def apply(self, allConfigs):
        commands = list()

        if self.mode == "ap":
            pass
        elif self.mode == "sta":
            # TODO: Implement "sta" mode.

            # We only need to set the channel in "sta" mode.  In "ap" mode,
            # hostapd will take care of it.
            #cmd = ["iw", "dev", wifiDevice.name, "set", "channel",
            #       str(wifiDevice.channel)]

            #commands.append(Command(cmd, self))
            raise Exception("WiFi sta mode not implemented")
        else:
            raise Exception("Unsupported mode ({}) in {}".format(
                self.mode, str(self)))

        # Look up the wifi-device section.
        wifiDevice = self.lookup(allConfigs, "wifi-device", self.device)

        # Look up the interface section.
        interface = self.lookup(allConfigs, "interface", self.network)

        self.isVirtual = True

        # Make this private variable because the real option variable (ifname)
        # should really be read-only.  Changing it breaks our equality checks.
        self._ifname = self.ifname

        if self.ifname == wifiDevice.name:
            # This interface is using the physical device directly (eg. wlan0).
            # This case is when the configuration specified the ifname option.
            self.isVirtual = False

            cmd = ["iw", "dev", wifiDevice.name, "set", "type", "__ap"]
            commands.append((self.PRIO_CONFIG_IFACE, Command(cmd, self)))

        elif interface.config_ifname == wifiDevice.name:
            # This interface is using the physical device directly (eg. wlan0).
            # TODO: Remove this case if it is not used.
            self._ifname = interface.config_ifname
            self.isVirtual = False

            cmd = ["iw", "dev", wifiDevice.name, "set", "type", "__ap"]
            commands.append((self.PRIO_CONFIG_IFACE, Command(cmd, self)))

        elif self.ifname is None:
            # This interface is a virtual one (eg. foo.wlan0 using wlan0).  Get
            # the virtual interface name from the network it's attached to.
            # This is unusual behavior which may be dropped in favor of
            # generating a name here.
            self._ifname = interface.config_ifname

        if self.isVirtual:
            # Command to create the virtual interface.
            cmd = ["iw", "dev", wifiDevice.name, "interface", "add",
                   self._ifname, "type", "__ap"]
            commands.append((self.PRIO_CREATE_IFACE, Command(cmd, self)))

            # Assign a random MAC address to avoid conflict with other
            # interfaces using the same device.
            cmd = ["ip", "link", "set", "dev", self._ifname,
                    "address", self.getRandomMAC()]
            commands.append((self.PRIO_CREATE_IFACE, Command(cmd, self)))

        confFile = self.makeHostapdConf(wifiDevice, interface)

        self.pidFile = "{}/hostapd-{}.pid".format(
            self.manager.writeDir, self.internalName)

        cmd = ["/apps/bin/hostapd", "-P", self.pidFile, "-B", confFile]
        commands.append((self.PRIO_START_DAEMON, Command(cmd, self)))

        return commands

    def makeHostapdConf(self, wifiDevice, interface):
        outputPath = "{}/hostapd-{}.conf".format(
            self.manager.writeDir, self.internalName)

        conf = HostapdConfGenerator(self, wifiDevice, interface)
        conf.generate(outputPath)

        return outputPath

    def revert(self, allConfigs):
        commands = list()

        commands.append((-self.PRIO_START_DAEMON,
            KillCommand(self.pidFile, self)))

        # Delete our virtual interface.
        if self.isVirtual:
            cmd = ["iw", "dev", self._ifname, "del"]
            commands.append((-self.PRIO_CREATE_IFACE, Command(cmd, self)))

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
            wifiDevice = new.lookup(allConfigs, "wifi-device", new.device)

            # Look up the interface section.
            interface = new.lookup(allConfigs, "interface", new.network)

            confFile = new.makeHostapdConf(wifiDevice, interface)

            new.pidFile = "{}/hostapd-{}.pid".format(
                new.manager.writeDir, self.internalName)

            cmd = ["/apps/bin/hostapd", "-P", new.pidFile, "-B", confFile]
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


class HostapdConfGenerator(object):
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

            options = self.get11nOptions()
            self.writeOptions(options, output, title="802.11n")

            options = self.get11acOptions()
            self.writeOptions(options, output, title="802.11ac")

            options = self.getSecurityOptions()
            self.writeOptions(options, output, title="Security")

    def getMainOptions(self):
        options = list()

        options.append(("interface", self.wifiIface._ifname))

        if self.interface.type == "bridge":
            options.append(("bridge", self.interface.config_ifname))

        options.append(("ssid", self.wifiIface.ssid))

        if self.wifiDevice.country is not None:
            options.append(("country_code", self.wifiDevice.country))
            options.append(("ieee80211d", 1))

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

        return options

    def get11nOptions(self):
        options = list()

        options.append(("ieee80211n", 1 * self.enable11n))

        if self.wifiDevice.htmode is None:
            pass
        elif self.wifiDevice.htmode.startswith("HT40"):
            # TODO: Add other ht_capab flags.
            options.append(("ht_capab", "[{}]".format(self.wifiDevice.htmode)))

        return options

    def get11acOptions(self):
        options = list()

        options.append(("ieee80211ac", 1 * self.enable11ac))

        # TODO: implement VHT settings to go above 40 MHz channel width

        return options

    def getSecurityOptions(self):
        options = list()

        if self.wifiIface.encryption is None or \
                self.wifiIface.encryption == "none":
            options.append(("wpa", 0))

        elif self.wifiIface.encryption == "psk2":
            options.append(("wpa", 1))

            # If key is a 64 character hex string, then treat it as the PSK
            # directly, else treat it as a passphrase.
            if len(self.wifiIface.key) == 64 and isHexString(self.wifiIface.key):
                options.append(("wpa_psk", self.wifiIface.key))
            else:
                options.append(("wpa_passphrase", self.wifiIface.key))

            # Encryption for WPA
            options.append(("wpa_pairwise", "TKIP"))

            # Encryption for WPA2
            options.append(("rsn_pairwise", "CCMP"))

        else:
            out.warn("Encryption type {} not supported (supported: "
                     "none|psk2)".format(self.wifiIface.encryption))
            raise Exception("Encryption type not supported")

        return options

    def writeHeader(self, output):
        output.write("#" * 80 + "\n")
        output.write("# hostapd configuration file generated by pdconf\n")
        output.write("# Source: {}\n".format(self.wifiIface.source))
        output.write("# Section: {}\n".format(str(self.wifiIface)))
        output.write("# Device: {}\n".format(str(self.wifiDevice)))
        output.write("# Interface: {}\n".format(str(self.interface)))
        output.write("#" * 80 + "\n")

    def writeOptions(self, options, output, title=None):
        output.write("\n")
        if title is not None:
            output.write("##### {} ##################################\n".format(title))
        for name, value in options:
            output.write("{}={}\n".format(name, value))
