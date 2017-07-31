from nose.tools import assert_raises
from mock import MagicMock, Mock, patch

from paradrop.core.config import network
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
