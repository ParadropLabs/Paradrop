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
import operator
import os
import re
import subprocess

from paradrop.base.output import out
from paradrop.base import settings
from paradrop.lib.utils import datastruct, pdos, uci
from paradrop.core.config import uciutils

IEEE80211_DIR = "/sys/class/ieee80211"
SYS_DIR = "/sys/class/net"
EXCLUDE_IFACES = set(["lo"])

# Strings that identify a virtual interface.
VIF_MARKERS = [".", "veth"]

# Matches various ways of specifying WiFi devices (phy0, wlan0).
WIFI_DEV_REF = re.compile("([a-z]+)(\d+)")

# Set of wifi-interface mode values that are handled by Paradrop rather than
# UCI configuration system.
WIFI_NONSTANDARD_MODES = set(["airshark"])


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

    Within each list, a device is represented by a dictionary.
    For all devices, the 'name' and 'mac' fields are defined.
    For WiFi devices, the 'phy' is defined in addition.
    Later, we may fill in more device information
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
    path = "{}/{}/macaddress".format(IEEE80211_DIR, phy)
    return readSysFile(path)


def getWirelessPhyName(ifname):
    path = "{}/{}/phy80211/name".format(SYS_DIR, ifname)
    return readSysFile(path)


class SysReader(object):
    def __init__(self, phy):
        self.phy = phy
        self.device_path = "{}/{}/device".format(IEEE80211_DIR, phy)

    def getDeviceId(self, default="????"):
        """
        Return the device ID for the device.

        This is a four-digit hexadecimal number.  For example, our Qualcomm
        802.11n chips have device ID 002a.
        """
        path = os.path.join(self.device_path, "device")
        device = readSysFile(path)
        if device is None:
            device = default
        return device

    def getSlotName(self, default=None):
        """
        Return the PCI slot name for the device.

        Example: "0000:04:00.0"
        """
        path = os.path.join(self.device_path, "uevent")
        with open(path, "r") as source:
            for line in source:
                key, value = line.split("=")
                if key == "PCI_SLOT_NAME":
                    return value
        return default

    def getVendorId(self, default="????"):
        """
        Return the vendor ID for the device.

        This is a four-digit hexadecimal number.  For example, our Qualcomm
        802.11n chips have vendor ID 168c.
        """
        path = os.path.join(self.device_path, "vendor")
        vendor = readSysFile(path)
        if vendor is None:
            vendor = default
        return vendor


def listWiFiDevices():
    # Collect information about the physical devices (e.g. phy0 -> MAC address,
    # device type, PCI slot, etc.) and store as objects in a dictionary.
    devices = dict()
    try:
        for phy in pdos.listdir(IEEE80211_DIR):
            mac = getPhyMACAddress(phy)
            reader = SysReader(phy)

            devices[phy] = {
                'name': "wifi{}".format(mac.replace(':', '')),
                'type': 'wifi',
                'mac': mac,
                'phy': phy,
                'vendor': reader.getVendorId(),
                'device': reader.getDeviceId(),
                'pci_slot': reader.getSlotName()
            }
    except OSError:
        # If we get an error here, it probably just means there are no WiFi
        # devices.
        pass

    # Collect a list of interfaces corresponding to each physical device
    # (e.g. phy0 -> wlan0, vwlan0.0000, etc.)
    interfaces = dict((dev, []) for dev in devices.keys())
    for ifname in pdos.listdir(SYS_DIR):
        try:
            path = "{}/{}/phy80211/name"
            phy = readSysFile(path)

            path = "{}/{}/ifindex"
            ifindex = int(readSysFile(path))

            interfaces[phy].append({
                'ifname': ifname,
                'ifindex': ifindex
            })
        except:
            # Error probably means it was not a wireless interface.
            pass

    # Sort by ifindex to identify the primary interface, which is the one that
    # was created when the device was first added.  We make use the fact that
    # Linux uses monotonically increasing ifindex values.
    for phy, device in devices.iteritems():
        if len(interfaces[phy]) > 0:
            interfaces[phy].sort(key=operator.itemgetter('ifindex'))
            device['primary_interface'] = interfaces[phy]['ifname']
        else:
            device['primary_interface'] = None

    # Finally, sort the device list by PCI slot to create an ordering that is
    # stable across device reboots and somewhat stable across hardware swaps.
    # TODO: sort PCI devices by pci_slot and USB devices by something else.
    result = devices.values()
    result.sort(key=operator.itemgetter('pci_slot'))

    pci_index = 0
    usb_index = 0
    for dev in result:
        if dev['pci_slot'] is not None:
            dev['id'] = "pci-wifi-{}".format(pci_index)
            pci_index += 1
        else:
            dev['id'] = "usb-wifi-{}".format(usb_index)
            usb_index += 1

    return result


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
        if ifname.startswith("sit"):
            continue

        dev = {
            'name': ifname,
            'mac': getMACAddress(ifname)
        }

        if isWAN(ifname):
            dev['type'] = 'wan'
        elif isWireless(ifname):
            # Detect wireless devices separately.
            continue
        else:
            dev['type'] = 'lan'

        devices.append(dev)

    wifi_devices = listWiFiDevices()
    devices.extend(wifi_devices)

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


def readHostconfigWifi(wifi, wirelessSections, networkDevices):
    for dev in wifi:
        # The preferred method is to use the id field, which could contain many
        # different kinds of identifiers (MAC address, phy, interface, or
        # index), and use the resolveWirelessDevRef to produce a MAC
        # address-based name.  resolve that to a MAC address-based name.  Most
        # importantly, index-based names here mean host configurations can be
        # copied to different machines, but then resolved unambiguously to
        # devices.
        #
        # We can also a few other forms of identification from older
        # configuration files (macaddr, phy, or interface) and convert to
        # MAC-based name.

        if 'id' in dev:
            resolved = resolveWirelessDevRef(dev['id'], networkDevices)
            mac = resolved['mac']
        elif 'macaddr' in dev:
            mac = dev['macaddr']
        elif 'phy' in dev:
            mac = getPhyMACAddress(dev['phy'])
        elif 'interface' in dev:
            phy = getWirelessPhyName(dev['interface'])
            mac = getPhyMACAddress(phy)
        else:
            raise Exception("Missing name or address field in wifi device definition.")

        config = {
            "type": "wifi-device",
            "name": "wifi{}".format(mac.replace(":", ""))
        }

        # We want to copy over all fields except name, interface, and phy.
        options = dev.copy()

        for key in ['id', 'interface', 'phy']:
            if key in options:
                del options[key]

        # Make sure macaddr is specified because that is the based way for
        # pdconf to identify the device.
        options['macaddr'] = mac

        # If type is missing, then add it because it is a required field.
        if 'type' not in options:
            options['type'] = 'auto'

        wirelessSections.append((config, options))


def resolveWirelessDevRef(name, networkDevices):
    """
    Resolve a WiFi device reference (wlan0, phy0, 00:11:22:33:44:55, etc.) to
    the name of the device section as used by pdconf (wifiXXXXXXXXXXXX).

    Unambiguous naming is preferred going forward (either wifiXX or the MAC
    address), but to maintain backward compatibility, we attempt to resolve
    either wlanX or phyX to the MAC address of the device that currently uses
    that name.
    """
    for device in networkDevices['wifi']:
        # Construct a set of accepted identifiers for this device.
        identifiers = set()

        # MAC-based identifiers, e.g. wifi001122334455 or 00:11:22:33:44:55
        identifiers.add(device['name'])
        identifiers.add(device['mac'])

        # Index-based with deterministic ordering, e.g. pci-wifi-0
        identifiers.add(device['id'])

        # Ambiguous identifiers, e.g. phy0 or wlan0
        identifiers.add(device['phy'])
        if device['primary_interface'] is not None:
            identifiers.add(device['primary_interface'])

        # If the given name matches anything in the current set, return the
        # device name.
        if name in identifiers:
            return device

    raise Exception("Could not resolve wireless device {}".format(name))


def readHostconfigWifiInterfaces(wifiInterfaces, wirelessSections, networkDevices):
    for iface in wifiInterfaces:
        # We handle nonstandard modes (e.g. Airshark) separately rather than
        # through the UCI system.
        if iface.get('mode', None) in WIFI_NONSTANDARD_MODES:
            continue

        config = {"type": "wifi-iface"}

        options = iface.copy()

        # There are various ways the host configuration file may have specified
        # the WiFi device (wlan0, phy0, pci-wifi-0, 00:11:22:33:44:55, etc.).
        # Try to resolve that to a device name that pdconf will recognize.
        try:
            device = resolveWirelessDevRef(options['device'], networkDevices)
            options['device'] = device['name']
        except:
            pass

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
    networkDevices = update.new.getCache('networkDevices')

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
                'domain': settings.LOCAL_DOMAIN
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
                'name': settings.LOCAL_DOMAIN,
                'ip': hostConfig['lan']['ipaddr']
            }
            dhcpSections.append((config, options))

        zoneFirewallSettings("lan")

        config = {"type": "interface", "name": "lan"}
        options = {
            "enabled": 0
        }
        qosSections.append((config, options))

    # Automatically generate loopback section.  There is generally not much to
    # configure for loopback, but we could add support to the host
    # configuration.
    config = {"type": "interface", "name": "loopback"}
    options = {
        'ifname': 'lo',
        'proto': 'static',
        'ipaddr': '127.0.0.1',
        'netmask': '255.0.0.0'
    }
    uciutils.setList(options, 'ifname', ['lo'])
    networkSections.append((config, options))

    config = {'type': 'zone'}
    options = {
        'name': 'loopback',
        'masq': '0',
        'conntrack': '1',
        'input': 'ACCEPT',
        'forward': 'ACCEPT',
        'output': 'ACCEPT'
    }
    uciutils.setList(options, 'network', ['loopback'])
    firewallSections.append((config, options))

    wifi = hostConfig.get('wifi', [])
    readHostconfigWifi(wifi, wirelessSections, networkDevices)

    wifiInterfaces = hostConfig.get('wifi-interfaces', [])
    readHostconfigWifiInterfaces(wifiInterfaces, wirelessSections, networkDevices)

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
