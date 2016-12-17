"""
Detect physical devices that can be used by chutes.

This module detects physical devices (for now just network interfaces) that can
be used by chutes.  This includes WAN interfaces for Internet connectivity and
WiFi interfaces which can host APs.

It also makes sure certain entries exist in the system UCI files for these
devices, for example "wifi-device" sections.  These are shared between chutes,
so they only need to be added when missing.
"""

import itertools
import os
import re
import subprocess

from paradrop.base.output import out
from paradrop.base import settings
from paradrop.lib.utils import datastruct, pdos, uci
from paradrop.lib.config import uciutils

IEEE80211_DIR = "/sys/class/ieee80211"
SYS_DIR = "/sys/class/net"
EXCLUDE_IFACES = set(["lo"])

# Strings that identify a virtual interface.
VIF_MARKERS = [".", "veth"]


def isVirtual(ifname):
    """
    Test if an interface is a virtual one.

    FIXME: This just tests for the presence of certain strings in the interface
    name, so it is not very robust.
    """
    for marker in VIF_MARKERS:
        if marker in ifname:
            return True
    return False


def isWAN(ifname):
    """
    Test if an interface is a WAN interface.
    """
    pattern = re.compile(r"(\w+)\s+(\w+)*")
    routeList = pdos.readFile("/proc/net/route")
    for line in routeList:
        match = pattern.match(line)
        if match is not None and \
                match.group(1) == ifname and \
                match.group(2) == "00000000":
            return True
    return False


def isWireless(ifname):
    """
    Test if an interface is a wireless device.
    """
    check_path = "{}/{}/wireless".format(SYS_DIR, ifname)
    return pdos.exists(check_path)


def detectSystemDevices():
    """
    Detect devices on the system.

    The result is three lists stored in a dictionary.  The three lists are
    indexed by 'wan', 'wifi', and 'lan'.  Other devices may be supported by
    adding additional lists.

    Within each list, a device is represented by a dictionary.  Currently, only
    the 'name' field is defined.  Later, we may fill in device information
    (e.g. what channels a WiFi card supports).
    """
    devices = dict()
    devices['wan'] = list()
    devices['wifi'] = list()
    devices['lan'] = list()

    for dev in listSystemDevices():
        devices[dev['type']].append(dev)
        del dev['type']

    return devices


def readSysFile(path):
    try:
        with open(path, 'r') as source:
            return source.read().strip()
    except:
        return None


def getMACAddress(ifname):
    path = "{}/{}/address".format(SYS_DIR, ifname)
    return readSysFile(path)


def getPhyMACAddress(phy):
    path = "{}/{}/address".format(IEEE80211_DIR, phy)
    return readSysFile(path)


def getWirelessPhyName(ifname):
    path = "{}/{}/phy80211/name".format(SYS_DIR, ifname)
    return readSysFile(path)


def getWirelessDeviceId(ifname):
    """
    Return the physical device ID for a wireless interface.

    This is will be a pair of hexadecimal numbers separated by a colon.  The
    first four digits are the vendor, and the second four our the device.
    You may find information about devices in /usr/share/hwdata/pci.ids.

    For example: our Qualcomm 802.11n chips have the ID 168c:002a.
    """
    path = "{}/{}/phy80211/device/vendor".format(SYS_DIR, ifname)
    vendor = readSysFile(path)
    if vendor is None:
        vendor = "????"

    path = "{}/{}/phy80211/device/device".format(SYS_DIR, ifname)
    device = readSysFile(path)
    if device is None:
        device = "????"

    return "{}:{}".format(vendor, device)


def listSystemDevices():
    """
    Detect devices on the system.

    The result is a single list of dictionaries, each containing information
    about a network device.
    """
    devices = list()
    detectedWifi = set()

    for ifname in pdos.listdir(SYS_DIR):
        if ifname in EXCLUDE_IFACES:
            continue

        # Only want to detect physical interfaces.
        if isVirtual(ifname):
            continue

        # More special cases to ignore for now.
        if ifname.startswith("br"):
            continue
        if ifname.startswith("docker"):
            continue

        dev = {
            'name': ifname,
            'mac': getMACAddress(ifname)
        }

        if isWAN(ifname):
            dev['type'] = 'wan'
        elif isWireless(ifname):
            dev['type'] = 'wifi'
            dev['phy'] = getWirelessPhyName(ifname)
            dev['ifname'] = ifname

            # For wireless devices, use the phy name because it is more stable.
            dev['name'] = dev['phy']

            detectedWifi.add(dev['phy'])
        else:
            dev['type'] = 'lan'

        devices.append(dev)

    for phy in pdos.listdir(IEEE80211_DIR):
        if phy not in detectedWifi:
            dev = {
                'name': phy,
                'type': 'wifi',
                'mac': getPhyMACAddress(phy),
                'phy': phy
            }
            detectedWifi.add(phy)
            devices.append(dev)

    return devices


def flushWirelessInterfaces(phy):
    """
    Remove all virtual interfaces associated with a wireless device.

    This should be used before giving a chute exclusive access to a device
    (e.g. monitor mode), so that it does not inherit unexpected interfaces.
    """
    for ifname in pdos.listdir(SYS_DIR):
        if ifname in EXCLUDE_IFACES:
            continue

        if getWirelessPhyName(ifname) == phy:
            cmd = ['iw', 'dev', ifname, 'del']
            subprocess.call(cmd)


def setConfig(chuteName, sections, filepath):
    cfgFile = uci.UCIConfig(filepath)

    # Set the name in the comment field.
    for config, options in sections:
        config['comment'] = chuteName

    oldSections = cfgFile.getChuteConfigs(chuteName)
    if not uci.chuteConfigsMatch(oldSections, sections):
        cfgFile.delConfigs(oldSections)
        cfgFile.addConfigs(sections)
        cfgFile.save(backupToken="paradrop", internalid=chuteName)
    else:
        # Save a backup of the file even though there were no changes.
        cfgFile.backup(backupToken="paradrop")


#
# Chute update functions
#


def getSystemDevices(update):
    """
    Detect devices on the system.

    Store device information in cache key "networkDevices".
    """
    devices = detectSystemDevices()
    update.new.setCache('networkDevices', devices)


def readHostconfigWifi(wifi, wirelessSections):
    for dev in wifi:
        # Old hostconfig blocks contained an 'interface'.  This is
        # deprecated in favor of 'phy' or 'ifname', which correspond to UCI
        # options.
        if 'phy' in dev:
            name = dev['phy']
        elif 'ifname' in dev:
            name = getWirelessPhyName(dev['ifname'])
        elif 'interface' in dev:
            # deprecated
            out.warn("Use of 'interface' field in 'wifi' section is deprecated.")
            name = getWirelessPhyName(dev['interface'])
        else:
            raise Exception("Missing phy/ifname field in hostconfig.")

        config = {
            "type": "wifi-device",
            "name": name
        }

        # We want to copy over all fields except interface.
        options = dev.copy()
        if 'interface' in options:
            del options['interface']

        # If type is missing, then add it because it is a required field.
        if 'type' not in options:
            options['type'] = 'auto'

        wirelessSections.append((config, options))


def readHostconfigWifiInterfaces(wifiInterfaces, wirelessSections):
    for iface in wifiInterfaces:
        config = {"type": "wifi-iface"}

        options = iface.copy()

        # Old hostconfig blocks used interface name for device.
        # Translate those to phy names, which are more stable.
        phy = getWirelessPhyName(options['device'])
        if phy is not None:
            out.warn("Use of interface name ({}) instead of device ({}) in wifi-interface section is deprecated.".format(options['device'], phy))
            options['device'] = phy

        wirelessSections.append((config, options))


def checkSystemDevices(update):
    """
    Check whether expected devices are present.

    This may reboot the machine if devices are missing and the host config is
    set to do that.
    """
    devices = update.new.getCache('networkDevices')
    hostConfig = update.new.getCache('hostConfig')

    if len(devices['wifi']) == 0:
        # No WiFi devices - check what we should do.
        action = datastruct.getValue(hostConfig, "system.onMissingWiFi")
        if action == "reboot":
            out.warn("No WiFi devices were detected, system will be rebooted.")
            cmd = ["shutdown", "-r", "now"]
            subprocess.call(cmd)

        elif action == "warn":
            out.warn("No WiFi devices were detected.")


def setSystemDevices(update):
    """
    Initialize system configuration files.

    This section should only be run for host configuration updates.

    Creates basic sections that all chutes require such as the "wan" interface.
    """
    hostConfig = update.new.getCache('hostConfig')

    dhcpSections = list()
    networkSections = list()
    firewallSections = list()
    wirelessSections = list()
    qosSections = list()

    # This section defines the default input, output, and forward policies for
    # the firewall.
    config = {"type": "defaults"}
    options = datastruct.getValue(hostConfig, "firewall.defaults", {})
    firewallSections.append((config, options))

    def zoneFirewallSettings(name):
        # Create zone entry with defaults (input, output, forward policies and
        # other configuration).
        #
        # Make a copy of the object from hostconfig because we modify it.
        config = {"type": "zone"}
        options = datastruct.getValue(hostConfig,
                name+".firewall.defaults", {}).copy()
        options['name'] = name
        uciutils.setList(options, 'network', [name])
        firewallSections.append((config, options))

        # Add forwarding entries (rules that allow traffic to move from one
        # zone to another).
        rules = datastruct.getValue(hostConfig, name+".firewall.forwarding", [])
        for rule in rules:
            config = {"type": "forwarding"}
            firewallSections.append((config, rule))

    if 'wan' in hostConfig:
        config = {"type": "interface", "name": "wan"}

        options = dict()
        options['ifname'] = hostConfig['wan']['interface']
        options['proto'] = "dhcp"

        networkSections.append((config, options))

        zoneFirewallSettings("wan")

        config = {"type": "interface", "name": "wan"}
        options = {
            "enabled": 0
        }
        qosSections.append((config, options))

    if 'lan' in hostConfig:
        config = {"type": "interface", "name": "lan"}

        options = dict()
        options['type'] = "bridge"
        options['bridge_empty'] = "1"

        options['proto'] = 'static'
        options['ipaddr'] = hostConfig['lan']['ipaddr']
        options['netmask'] = hostConfig['lan']['netmask']
        uciutils.setList(options, 'ifname', hostConfig['lan']['interfaces'])

        networkSections.append((config, options))

        if 'dhcp' in hostConfig['lan']:
            dhcp = hostConfig['lan']['dhcp']

            config = {'type': 'dnsmasq'}
            options = {
                'interface': 'lan',
                'domain': 'home.paradrop.org'
            }
            dhcpSections.append((config, options))

            config = {'type': 'dhcp', 'name': 'lan'}
            options = {
                'interface': 'lan',
                'start': dhcp['start'],
                'limit': dhcp['limit'],
                'leasetime': dhcp['leasetime']
            }
            dhcpSections.append((config, options))

            config = {'type': 'domain'}
            options = {
                'name': 'home.paradrop.org',
                'ip': hostConfig['lan']['ipaddr']
            }
            dhcpSections.append((config, options))

        zoneFirewallSettings("lan")

        config = {"type": "interface", "name": "lan"}
        options = {
            "enabled": 0
        }
        qosSections.append((config, options))

    if 'wifi' in hostConfig:
        for dev in hostConfig['wifi']:
            if 'phy' in dev:
                name = dev['phy']
            elif 'ifname' in dev:
                name = getWirelessPhyName(dev['ifname'])
            elif 'interface' in dev:
                # deprecated
                out.warn("Use of 'interface' field in 'wifi' section is deprecated.")
                name = getWirelessPhyName(dev['interface'])
            else:
                raise Exception("Missing phy/ifname field in hostconfig.")

            config = {
                "type": "wifi-device",
                "name": name
            }

            # We want to copy over all fields except interface.
            options = dev.copy()
            if 'interface' in options:
                del options['interface']

            # If type is missing, then add it because it is a required field.
            if 'type' not in options:
                options['type'] = 'auto'

    wifi = hostConfig.get('wifi', [])
    readHostconfigWifi(wifi, wirelessSections)

    wifiInterfaces = hostConfig.get('wifi-interfaces', [])
    readHostconfigWifiInterfaces(wifiInterfaces, wirelessSections)

    # Add additional firewall rules.
    rules = datastruct.getValue(hostConfig, "firewall.rules", [])
    for rule in rules:
        config = {"type": "rule"}
        firewallSections.append((config, rule))

    setConfig(settings.RESERVED_CHUTE, dhcpSections,
              uci.getSystemPath("dhcp"))
    setConfig(settings.RESERVED_CHUTE, networkSections,
              uci.getSystemPath("network"))
    setConfig(settings.RESERVED_CHUTE, firewallSections,
              uci.getSystemPath("firewall"))
    setConfig(settings.RESERVED_CHUTE, wirelessSections,
              uci.getSystemPath("wireless"))
    setConfig(settings.RESERVED_CHUTE, qosSections,
              uci.getSystemPath("qos"))
