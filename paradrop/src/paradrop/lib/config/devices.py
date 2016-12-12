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
from paradrop.lib.utils import datastruct, pdos, uci
from paradrop.lib.misc import settings
from paradrop.lib.config import uciutils


SYS_DIR = "/sys/class/net"
EXCLUDE_IFACES = set(["lo"])
CHANNELS = [1, 6, 11]

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


def getMACAddress(ifname):
    path = "{}/{}/address".format(SYS_DIR, ifname)
    try:
        with open(path, 'r') as source:
            return source.read().strip()
    except:
        return None


def listSystemDevices():
    """
    Detect devices on the system.

    The result is a single list of dictionaries, each containing information
    about a network device.
    """
    devices = list()

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
        else:
            dev['type'] = 'lan'

        devices.append(dev)

    return devices


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
            config = {"type": "wifi-device", "name": dev['interface']}

            # We want to copy over all fields except interface.
            options = dev.copy()
            del options['interface']

            # If type is missing, then add it because it is a required field.
            if 'type' not in options:
                options['type'] = 'auto'

            wirelessSections.append((config, options))

    if 'wifi-interfaces' in hostConfig:
        for iface in hostConfig['wifi-interfaces']:
            config = {"type": "wifi-iface"}
            wirelessSections.append((config, iface))

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
