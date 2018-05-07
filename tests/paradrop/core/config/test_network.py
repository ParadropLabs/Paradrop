import collections
import netifaces
import ipaddress

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

    update.cache_set('deviceReservations', {})
    update.cache_set('interfaceReservations', set())
    update.cache_set('subnetReservations', set())

    update.state = "running"

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
    value = update.cache_get('networkInterfaces')
    assert isinstance(value, list) and len(value) == 1

    # Should have passed through the dhcp section.
    iface = value[0]
    assert 'dhcp' in iface


def test_get_current_phy_conf():
    hostConfig = {
        'wifi': [
            {'id': 'pci-wifi-0'}
        ]
    }

    update = MagicMock()
    update.cache_get.return_value = hostConfig

    result = network.get_current_phy_conf(update, 'pci-wifi-0')
    assert result['id'] == 'pci-wifi-0'

    result = network.get_current_phy_conf(update, 'notfound')
    assert result == {}


def test_satisfies_requirements():
    obj = {
        'x': 1,
        'y': 2,
        'z': 3
    }

    assert network.satisfies_requirements(obj, {})
    assert network.satisfies_requirements(obj, obj)

    assert network.satisfies_requirements(obj, {'x': 1})
    assert network.satisfies_requirements(obj, {'x': 1, 'y': 2})

    assert network.satisfies_requirements(obj, {'a': 1}) is False
    assert network.satisfies_requirements(obj, {'x': 2}) is False


def test_fulfillDeviceRequest():
    update = MagicMock()

    reservations = collections.defaultdict(DeviceReservations)
    update.cache_get.return_value = reservations

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
    update.cache_get.return_value = reservations

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
    update.cache_get.return_value = reservations

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


def test_fulfillDeviceRequest_additional_requests():
    """
    Test additional requests passed with the configuration.

    This test setup has two radios configured on different spectrum bands.
    The first AP interface has no requests and is assigned to the first
    device. The second AP requests a specific hardware (2.4 GHz) and is
    assigned to the second device.
    """
    reservations = collections.defaultdict(DeviceReservations)

    hostConfig = {
        'wifi': [
            {'id': 'pci-wifi-0', 'hwmode': '11a'},
            {'id': 'pci-wifi-1', 'hwmode': '11g'}
        ]
    }

    def getCache(key):
        if key == "deviceReservations":
            return reservations
        elif key == "hostConfig":
            return hostConfig

    update = MagicMock()
    update.cache_get.side_effect = getCache

    config1 = {
        'type': 'wifi',
        'mode': 'ap'
    }

    config2 = {
        'type': 'wifi',
        'mode': 'ap',
        'requests': {
            'hwmode': '11g'
        }
    }

    devices = {
        'wifi': [
            {'id': 'pci-wifi-0', 'name': 'wlan0'},
            {'id': 'pci-wifi-1', 'name': 'wlan1'}
        ]
    }

    result = network.fulfillDeviceRequest(update, config1, devices)
    assert result['id'] == 'pci-wifi-0'
    result = network.fulfillDeviceRequest(update, config2, devices)
    assert result['id'] == 'pci-wifi-1'


@patch("paradrop.core.config.network.chooseSubnet")
def test_getInterfaceAddress(chooseSubnet):
    chooseSubnet.return_value = ipaddress.ip_network(u"192.168.30.0/24")

    update = MagicMock()
    name = "test"
    cfg = MagicMock()
    iface = dict()
    network.getInterfaceAddress(update, name, cfg, iface)

    assert iface['subnet'] == chooseSubnet.return_value
    assert iface['netmask'] == "255.255.255.0"
    assert iface['externalIpaddr'] == "192.168.30.1"
    assert iface['internalIpaddr'] == "192.168.30.2"
    assert iface['ipaddrWithPrefix'] == "192.168.30.2/24"


@patch("paradrop.core.config.network.netifaces.ifaddresses")
def test_select_chute_subnet_pool(ifaddresses):
    host_config = {
        'wan': {
            'interface': 'eth0'
        },
        'system': {
            'chuteSubnetPool': 'auto'
        }
    }

    # Mock ifaddresses as if WAN interface has 192.x.x.x address.
    ifaddrs = {
        netifaces.AF_INET: [
            { 'addr': '192.168.1.20' }
        ]
    }
    ifaddresses.return_value = ifaddrs

    pool = network.select_chute_subnet_pool(host_config)
    assert pool.startswith("10.")

    # Mock ifaddresses as if WAN interface has 10.x.x.x address.
    ifaddrs[netifaces.AF_INET] = [{ 'addr': '10.42.0.20' }]

    pool = network.select_chute_subnet_pool(host_config)
    assert pool.startswith("192.168.")

    # Test static assignment.
    host_config['system']['chuteSubnetPool'] = '192.168.128.0/17'
    pool = network.select_chute_subnet_pool(host_config)
    assert pool == '192.168.128.0/17'
