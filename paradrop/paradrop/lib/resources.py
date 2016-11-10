"""
Module for checking resource reservations by chutes.

One idea motivating this design is to reduce the amount of state
in memory for resource reservations.  We have the chute list, which
contains information about what devices the chute is using.  If we also
maintain a separate list of devices used by chutes, we need to keep
them synchronized.  This becomes messy when a chute fails to install
or uninstall correctly.  The getDeviceReservations function iterates
over the chute list and returns an up-to-date view of device usage.
This can be called as needed.
"""
import collections

from paradrop.backend.fc.chutestorage import ChuteStorage
from paradrop.lib.config.devices import getWirelessPhyName
from paradrop.lib.config.hostconfig import prepareHostConfig


class DeviceReservations(object):
    def __init__(self):
        self.reservations = []

    def add(self, chute, dtype, mode=None):
        r = {
            'chute': chute,
            'type': dtype,
            'mode': mode
        }

        self.reservations.append(r)

    def count(self, dtype=None, mode=None):
        """
        Return the number of reservations matching the given criteria.

        None is used as a wildcard, so if no arguments are passed, the count
        returned is the total number of reservations.
        """
        count = 0
        for res in self.reservations:
            if dtype is not None and dtype != res['type']:
                continue
            if mode is not None and mode != res['mode']:
                continue
            count += 1
        return count


def getDeviceReservations():
    """
    Produce a dictionary mapping device names to DeviceReservations objects
    that describe the current usage of the device.

    The returned type is a defaultdict, so there is no need to check if a key
    exists before accessing it.
    """
    reservations = collections.defaultdict(DeviceReservations)

    hostConfig = prepareHostConfig()
    wifiInterfaces = hostConfig.get('wifi-interfaces', [])
    for iface in wifiInterfaces:
        if 'device' not in iface:
            continue

        dev = iface['device']
        phy = getWirelessPhyName(dev)
        if phy is not None:
            # It is annoying to do this conversion everywhere, but it would
            # be painful to break compatibility with all of the devices out
            # there that use e.g. wlan0 instead of phy0 in their hostconfig.
            dev = phy

        reservations[dev].add('__PARADROP__', 'wifi',
                iface.get('mode', 'ap'))

    for chute in ChuteStorage.chuteList.values():
        for iface in chute.getCache('networkInterfaces'):
            dev = iface['device']
            reservations[dev].add(chute.name, iface['netType'],
                    iface.get('mode', None))

    return reservations


def getInterfaceReservations():
    reservations = set()

    hostConfig = prepareHostConfig()
    wifiInterfaces = hostConfig.get('wifi-interfaces', [])
    for iface in wifiInterfaces:
        if 'ifname' not in iface:
            continue

        ifname = iface['ifname']
        reservations.add(ifname)

    for chute in ChuteStorage.chuteList.values():
        for iface in chute.getCache('networkInterfaces'):
            if 'externalIntf' not in iface:
                continue

            ifname = iface['externalIntf']
            reservations.add(ifname)

    return reservations


def getSubnetReservations():
    reservations = set()

    for chute in ChuteStorage.chuteList.values():
        for iface in chute.getCache('networkInterfaces'):
            if 'subnet' not in iface:
                continue

            subnet = iface['subnet']
            reservations.add(subnet)

    return reservations
