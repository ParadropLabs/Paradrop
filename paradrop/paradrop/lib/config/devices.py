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

from paradrop.lib.utils import uci
from pdtools.lib.output import out

SYS_DIR = "/sys/class/net"
EXCLUDE_IFACES = set(["lo"])
CHANNELS = [1, 6, 11]

# Special chute name that indicates these are system rules.
SYSTEM_CHUTE = "__PARADROP__"


def isWAN(ifname):
    """
    Test if an interface is a WAN interface.
    """
    pattern = re.compile("(\w+)\s+(\w+)*")
    with open("/proc/net/route", "r") as routeList:
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
    return os.path.exists(check_path)


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
    devices = dict()
    devices['wan'] = list()
    devices['wifi'] = list()

    for ifname in os.listdir(SYS_DIR):
        if ifname in EXCLUDE_IFACES:
            continue

        dev = {"name": ifname}

        if isWAN(ifname):
            devices['wan'].append(dev)

        if isWireless(ifname):
            devices['wifi'].append(dev)

    update.new.setCache('networkDevices', devices)


def setSystemDevices(update):
    """
    Initialize system configuration files.

    Creates basic sections that all chutes require such as the "wan" interface.
    """
    devices = update.new.getCache('networkDevices')
    if devices is None:
        return

    if len(devices['wan']) == 0:
        out.warn("No WAN interface found; "
                 "chute may not have Internet connectivity.")
    if len(devices['wifi']) == 0:
        out.warn("No available wireless interfaces found.")

    networkSections = list()
    firewallSections = list()
    wirelessSections = list()

    if len(devices['wan']) >= 1:
        # Only use one WAN device for now.
        wanDev = devices['wan'][0]

        config = {"type": "interface", "name": "wan"}
        options = {"ifname": wanDev['name'], "proto": "dhcp"}
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

    # Cycle through the channel list to assign different channels to
    # WiFi interfaces.
    channels = itertools.cycle(CHANNELS)

    for dev in devices['wifi']:
        config = {"type": "wifi-device", "name": dev['name']}
        options = {"type": "auto", "channel": channels.next()}
        wirelessSections.append((config, options))

    setConfig(SYSTEM_CHUTE, networkSections,
              uci.getSystemPath("network"))
    setConfig(SYSTEM_CHUTE, firewallSections,
              uci.getSystemPath("firewall"))
    setConfig(SYSTEM_CHUTE, wirelessSections,
              uci.getSystemPath("wireless"))
