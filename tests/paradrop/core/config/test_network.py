from nose.tools import assert_raises
from mock import MagicMock, Mock, patch

from paradrop.core.config import network


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
    update = MagicMock()
    update.old = None

    update.new.net = {
        'wifi': {
            'dhcp': {}
        }
    }

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
    args, kwargs = update.new.setCache.call_args
    key, value = args
    assert key == 'networkInterfaces'
    assert isinstance(value, list) and len(value) == 1

    # Should have passed through the dhcp section.
    iface = value[0]
    assert 'dhcp' in iface
