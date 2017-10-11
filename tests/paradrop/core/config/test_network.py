import collections
from nose.tools import assert_raises
from mock import MagicMock, Mock, patch

from paradrop.core.config import network
from paradrop.core.config.reservations import DeviceReservations
from paradrop.core.update.update_object import UpdateObject


def test_getInterfaceDict():
    # getInterfaceDict should be able to handle null chute.
    assert network.getInterfaceDict(None) == {}

    chute = MagicMock()
    chute.getCache.return_value = []
    assert network.getInterfaceDict(chute) == {}

    chute = MagicMock()
    chute.getCache.return_value = [
        {'name': 'eth0'},
        {'name': 'eth1'}
    ]
    ifaces = network.getInterfaceDict(chute)
    assert 'eth0' in ifaces
    assert 'eth1' in ifaces


def test_getNetworkConfigWifi():
    update = MagicMock()
    cfg = MagicMock()
    iface = {
        'device': 'verylongdevice'
    }

    # Exception: Interface name is too long
    assert_raises(Exception, network.getNetworkConfigWifi, update, "test", cfg, iface)


def test_getNetworkConfig():
    update = UpdateObject({'name': 'test'})
    update.old = None

    update.new.net = {
        'wifi': {
            'dhcp': {}
        }
    }

    update.new.setCache('deviceReservations', {})
    update.new.setCache('interfaceReservations', set())
    update.new.setCache('subnetReservations', set())

    # Exception: Interafce definition missing field(s)
    assert_raises(Exception, network.getNetworkConfig, update)

    update.new.net = {
        'vlan': {
            'intfName': 'eth1',
            'type': 'vlan',
            'dhcp': {},
            'vlan_id': 5
        }
    }

    network.getNetworkConfig(update)

    # Should have called setCache with a list containing one interface.
    value = update.new.getCache('networkInterfaces')
    assert isinstance(value, list) and len(value) == 1

    # Should have passed through the dhcp section.
    iface = value[0]
    assert 'dhcp' in iface


def test_fulfillDeviceRequest():
    update = MagicMock()

    reservations = collections.defaultdict(DeviceReservations)
    update.new.getCache.return_value = reservations

    devices = {
        'wifi': [
            {'name': 'wlan0'},
            {'name': 'wlan1'}
        ],
        'lan': [
            {'name': 'eth0'},
            {'name': 'eth1'}
        ]
    }

    # Test exclusive access type interfaces (monitor).
    #
    # The first interface is assigned to the first device, second interface
    # to the second device, and the third raises an exception.

    config = {
        'type': 'wifi',
        'mode': 'monitor'
    }

    result = network.fulfillDeviceRequest(update, config, devices)
    assert result['name'] == 'wlan0'
    result = network.fulfillDeviceRequest(update, config, devices)
    assert result['name'] == 'wlan1'
    assert_raises(Exception, network.fulfillDeviceRequest, update, config, devices)

    reservations = collections.defaultdict(DeviceReservations)
    update.new.getCache.return_value = reservations

    # Test shared access type interfaces (AP).
    #
    # This should assign several consecutive interfaces to the first device,
    # then to the second, then finally raise an exception.

    config = {
        'type': 'wifi',
        'mode': 'ap'
    }

    for i in range(network.MAX_AP_INTERFACES):
        result = network.fulfillDeviceRequest(update, config, devices)
        print(result)
        assert result['name'] == 'wlan0'
    for i in range(network.MAX_AP_INTERFACES):
        result = network.fulfillDeviceRequest(update, config, devices)
        assert result['name'] == 'wlan1'
    assert_raises(Exception, network.fulfillDeviceRequest, update, config, devices)

    reservations = collections.defaultdict(DeviceReservations)
    update.new.getCache.return_value = reservations

    # Test mixed assignment.
    #
    # The first interface gains exclusive access to the first device.
    # Following interfaces gain shared access to the second device.

    config = {
        'type': 'wifi',
        'mode': 'monitor'
    }

    result = network.fulfillDeviceRequest(update, config, devices)
    assert result['name'] == 'wlan0'

    config = {
        'type': 'wifi',
        'mode': 'ap'
    }

    for i in range(network.MAX_AP_INTERFACES):
        result = network.fulfillDeviceRequest(update, config, devices)
        print(result)
        assert result['name'] == 'wlan1'
    assert_raises(Exception, network.fulfillDeviceRequest, update, config, devices)

    # Test lan type interfaces.

    config = {
        'type': 'lan'
    }

    result = network.fulfillDeviceRequest(update, config, devices)
    assert result['name'] == 'eth0'
    result = network.fulfillDeviceRequest(update, config, devices)
    assert result['name'] == 'eth1'
    assert_raises(Exception, network.fulfillDeviceRequest, update, config, devices)
