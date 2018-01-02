import netifaces

from nose.tools import assert_raises
from mock import MagicMock, Mock, patch

from paradrop.core.config import devices


@patch("paradrop.core.config.devices.getPhyMACAddress")
@patch("paradrop.core.config.devices.getWirelessPhyName")
def test_readHostconfigWifi(getWirelessPhyName, getPhyMACAddress):
    wifi = [{
        "interface": "wlan1",
        "channel": 1
    }]

    getWirelessPhyName.side_effect = lambda x: ("phy." + x)
    getPhyMACAddress.returns = "00:00:00:00:00:00"

    builder = devices.UCIBuilder()
    networkDevices = dict()
    devices.readHostconfigWifi(wifi, networkDevices, builder)

    sections = builder.getSections("wireless")
    assert len(sections) == 1
    config, options = sections[0]
    assert config['type'] == 'wifi-device'
    assert config['name'].startswith('wifi')

    wifi = [{
        "phy": "phy0",
        "channel": 6
    }]

    builder = devices.UCIBuilder()
    devices.readHostconfigWifi(wifi, networkDevices, builder)

    sections = builder.getSections("wireless")
    assert len(sections) == 1
    config, options = sections[0]
    assert config['type'] == 'wifi-device'
    assert config['name'].startswith('wifi')


@patch("paradrop.core.config.devices.getWirelessPhyName")
def test_readHostconfigWifiInterfaces(getWirelessPhyName):
    builder = devices.UCIBuilder()

    wifiInterfaces = [{
        "device": "wifi000000000000",
        "ifname": "wlan1",
        "ssid": "paradrop",
        "mode": "ap",
        "network": "lan"
    }]

    getWirelessPhyName.side_effect = lambda x: ("phy." + x)

    wirelessSections = list()
    networkDevices = dict()
    devices.readHostconfigWifiInterfaces(wifiInterfaces, networkDevices, builder)

    sections = builder.getSections("wireless")
    assert len(sections) == 1
    config, options = sections[0]
    assert config['type'] == 'wifi-iface'
    assert options['device'] == 'wifi000000000000'


def test_readHostconfigVlan():
    builder = devices.UCIBuilder()

    vlanInterfaces = [{
        'id': 2,
        'name': 'test',
        'proto': 'static',
        'ipaddr': '192.168.2.1',
        'netmask': '255.255.255.0',
        'dhcp': {
            'leasetime': '12h',
            'limit': 100,
            'start': 100,
        },
        'firewall': {
            'defaults': {
                'forward': 'REJECT',
                'input': 'ACCEPT',
                'output': 'ACCEPT'
            }
        }
    }]

    devices.readHostconfigVlan(vlanInterfaces, builder)

    sections = builder.getSections("firewall")
    assert len(sections) >= 1


@patch("paradrop.core.config.devices.netifaces.ifaddresses")
def test_select_brlan_address(ifaddresses):
    host_config = {
        'wan': {
            'interface': 'eth0'
        },
        'lan': {
            'proto': 'auto'
        }
    }

    # Mock ifaddresses as if WAN interface has 192.x.x.x address.
    ifaddrs = {
        netifaces.AF_INET: [
            { 'addr': '192.168.1.20' }
        ]
    }
    ifaddresses.return_value = ifaddrs

    addr, netmask = devices.select_brlan_address(host_config)
    assert addr.startswith("10.")

    # Mock ifaddresses as if WAN interface has 10.x.x.x address.
    ifaddrs[netifaces.AF_INET] = [{ 'addr': '10.42.0.20' }]

    addr, netmask = devices.select_brlan_address(host_config)
    assert addr.startswith("192.168.")

    # Test static assignment.
    host_config['lan']['proto'] = 'static'
    host_config['lan']['ipaddr'] = '192.168.1.1'
    host_config['lan']['netmask'] = '255.255.255.0'
    addr, netmask = devices.select_brlan_address(host_config)
    assert addr == '192.168.1.1'
    assert netmask == '255.255.255.0'
