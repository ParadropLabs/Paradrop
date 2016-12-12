from nose.tools import assert_raises
from mock import MagicMock, Mock, patch

from paradrop.lib.config import devices


@patch("paradrop.lib.config.devices.getWirelessPhyName")
def test_readHostconfigWifi(getWirelessPhyName):
    wifi = [{
        "interface": "wlan1",
        "channel": 1
    }]

    getWirelessPhyName.side_effect = lambda x: ("phy." + x)

    wirelessSections = list()
    devices.readHostconfigWifi(wifi, wirelessSections)

    assert len(wirelessSections) == 1
    config, options = wirelessSections[0]
    assert config['type'] == 'wifi-device'
    assert config['name'] == 'phy.wlan1'

    wifi = [{
        "phy": "phy0",
        "channel": 6
    }]

    wirelessSections = list()
    devices.readHostconfigWifi(wifi, wirelessSections)

    assert len(wirelessSections) == 1
    config, options = wirelessSections[0]
    assert config['type'] == 'wifi-device'
    assert config['name'] == 'phy0'


@patch("paradrop.lib.config.devices.getWirelessPhyName")
def test_readHostconfigWifiInterfaces(getWirelessPhyName):
    wifiInterfaces = [{
        "device": "wlan1",
        "ifname": "wlan1",
        "ssid": "paradrop",
        "mode": "ap",
        "network": "lan"
    }]

    getWirelessPhyName.side_effect = lambda x: ("phy." + x)

    wirelessSections = list()
    devices.readHostconfigWifiInterfaces(wifiInterfaces, wirelessSections)

    assert len(wirelessSections) == 1
    config, options = wirelessSections[0]
    assert config['type'] == 'wifi-iface'
    assert options['device'] == 'phy.wlan1'
