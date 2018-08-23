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
import ipaddress


from paradrop.base import constants
from paradrop.core.config.devices import getWirelessPhyName
from paradrop.core.config.hostconfig import prepareHostConfig
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.lib.utils import datastruct


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


def getDeviceReservations(exclude=None):
    """
    Produce a dictionary mapping device names to DeviceReservations objects
    that describe the current usage of the device.

    The returned type is a defaultdict, so there is no need to check if a key
    exists before accessing it.

    exclude: name of chute whose device reservations should be excluded
    """
    reservations = collections.defaultdict(DeviceReservations)

    if exclude != constants.RESERVED_CHUTE_NAME:
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

            reservations[dev].add(constants.RESERVED_CHUTE_NAME, 'wifi',
                    iface.get('mode', 'ap'))

        lanInterfaces = datastruct.getValue(hostConfig, 'lan.interfaces', [])
        for iface in lanInterfaces:
            reservations[iface].add(constants.RESERVED_CHUTE_NAME, 'lan', None)

    for chute in ChuteStorage.chuteList.values():
        if chute.name == exclude:
            continue

        for iface in chute.getCache('networkInterfaces'):
            dev = iface.get('device', None)

            # Device is not set in cases such as vlan interfaces.
            if dev is None:
                continue

            reservations[dev].add(chute.name, iface['type'],
                    iface.get('mode', None))

    return reservations


class InterfaceReservationSet(object):
    def __init__(self):
        self.reservations = set()

    def add(self, interface):
        self.reservations.add(interface)

    def __contains__(self, x):
        return x in self.reservations

    def __len__(self):
        return len(self.reservations)


def getInterfaceReservations(exclude=None):
    """
    Get current set of interface reservations.

    Returns an instance of InterfaceReservationSet.

    exclude: name of chute whose interfaces should be excluded
    """
    reservations = InterfaceReservationSet()

    if exclude != constants.RESERVED_CHUTE_NAME:
        hostConfig = prepareHostConfig()
        wifiInterfaces = hostConfig.get('wifi-interfaces', [])
        for iface in wifiInterfaces:
            if 'ifname' not in iface:
                continue

            ifname = iface['ifname']
            reservations.add(ifname)

    for chute in ChuteStorage.chuteList.values():
        if chute.name == exclude:
            continue

        for iface in chute.getCache('networkInterfaces'):
            if 'externalIntf' not in iface:
                continue

            ifname = iface['externalIntf']
            reservations.add(ifname)

    return reservations


class SubnetReservationSet(object):
    def __init__(self):
        self.reservations = []

    def add(self, subnet):
        self.reservations.append(subnet)

    def __contains__(self, subnet):
        for res in self.reservations:
            if res.overlaps(subnet):
                return True
        return False

    def __len__(self):
        return len(self.reservations)


def getSubnetReservations(exclude=None):
    """
    Get current set of subnet reservations.

    Returns an instance of SubnetReservationSet.

    exclude: name of chute whose reservations should be excluded
    """
    reservations = SubnetReservationSet()

    if exclude != constants.RESERVED_CHUTE_NAME:
        hostConfig = prepareHostConfig()
        ipaddr = datastruct.getValue(hostConfig, 'lan.ipaddr', None)
        netmask = datastruct.getValue(hostConfig, 'lan.netmask', None)
        if ipaddr is not None and netmask is not None:
            network = ipaddress.ip_network(u'{}/{}'.format(ipaddr, netmask),
                    strict=False)
            reservations.add(network)

    for chute in ChuteStorage.chuteList.values():
        if chute.name == exclude:
            continue

        for iface in chute.getCache('networkInterfaces'):
            if 'subnet' not in iface:
                continue

            subnet = iface['subnet']
            reservations.add(subnet)

    return reservations


def getReservations(update):
    """
    Get device and resource reservations claimed by other users.
    """
    devices = getDeviceReservations(exclude=update.new.name)
    interfaces = getInterfaceReservations(exclude=update.new.name)
    subnets = getSubnetReservations(exclude=update.new.name)

    update.cache_set('deviceReservations', devices)
    update.cache_set('interfaceReservations', interfaces)
    update.cache_set('subnetReservations', subnets)
