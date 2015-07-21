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
            if match.group(1) == ifname and match.group(2) == "00000000":
                return True
    return False


def isWireless(ifname):
    """
    Test if an interface is a wireless device.
    """
    check_path = "{}/{}/wireless".format(SYS_DIR, ifname)
    return os.path.exists(check_path)


def setupSystemConfig(update):
    """
    Initialize system configuration files.

    Creates basic sections that all chutes require such as the "wan" interface.
    """
    # Cycle through the channel list to assign different channels to
    # WiFi interfaces.
    channels = itertools.cycle(CHANNELS)

    # Only want one WAN interface for now.
    wanFound = False

    networkSections = list()
    firewallSections = list()
    wirelessSections = list()

    for ifname in os.listdir(SYS_DIR):
        if ifname in EXCLUDE_IFACES:
            continue

        wan = isWAN(ifname)
        if not wanFound and wan:
            config = {"type": "interface", "name": "wan"}
            options = {"ifname": ifname, "proto": "dhcp"}
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

            wanFound = True

        if not wan and isWireless(ifname):
            config = {"type": "wifi-device", "name": ifname}
            options = {"type": "auto", "channel": channels.next()}
            wirelessSections.append((config, options))

    if not wanFound:
        out.warn("No WAN interface found.")
    if len(wirelessSections) == 0:
        out.warn("No available wireless interfaces found.")

    setConfig(SYSTEM_CHUTE, networkSections,
              uci.getSystemPath("network"))
    setConfig(SYSTEM_CHUTE, firewallSections,
              uci.getSystemPath("firewall"))
    setConfig(SYSTEM_CHUTE, wirelessSections,
              uci.getSystemPath("wireless"))


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
