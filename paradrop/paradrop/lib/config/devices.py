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

from paradrop.lib.utils import pdos, uci
from pdtools.lib.output import out
from paradrop.lib import settings
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

        dev = {"name": ifname}

        if isWAN(ifname):
            devices['wan'].append(dev)
        elif isWireless(ifname):
            devices['wifi'].append(dev)
        else:
            devices['lan'].append(dev)

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
        cfgFile.save(internalid=chuteName)


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


def setSystemDevices(update):
    """
    Initialize system configuration files.

    Creates basic sections that all chutes require such as the "wan" interface.
    """
    hostConfig = update.new.getCache('hostConfig')

    dhcpSections = list()
    networkSections = list()
    firewallSections = list()
    wirelessSections = list()

    if 'wan' in hostConfig:
        config = {"type": "interface", "name": "wan"}

        options = dict()
        options['ifname'] = hostConfig['wan']['interface']
        options['proto'] = "dhcp"

        networkSections.append((config, options))

        config = {"type": "zone"}
        options = {
            "name": "wan",
            "masq": "1",
            "input": "ACCEPT",
            "forward": "REJECT",
            "output": "ACCEPT",
            "network": "wan"
        }
        firewallSections.append((config, options))

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
            options = {'interface': 'lan'}

            dhcpSections.append((config, options))

            config = {'type': 'dhcp', 'name': 'lan'}
            options = {
                'interface': 'lan',
                'start': dhcp['start'],
                'limit': dhcp['limit'],
                'leasetime': dhcp['leasetime']
            }

            dhcpSections.append((config, options))

    if 'wifi' in hostConfig:
        for dev in hostConfig['wifi']:
            config = {"type": "wifi-device", "name": dev['interface']}
            options = {
                'type': 'auto',
                'channel': dev['channel']
            }

            wirelessSections.append((config, options))

    if 'wifi-interfaces' in hostConfig:
        for iface in hostConfig['wifi-interfaces']:
            config = {"type": "wifi-iface"}
            wirelessSections.append((config, iface))

    setConfig(settings.RESERVED_CHUTE, dhcpSections,
              uci.getSystemPath("dhcp"))
    setConfig(settings.RESERVED_CHUTE, networkSections,
              uci.getSystemPath("network"))
    setConfig(settings.RESERVED_CHUTE, firewallSections,
              uci.getSystemPath("firewall"))
    setConfig(settings.RESERVED_CHUTE, wirelessSections,
              uci.getSystemPath("wireless"))
