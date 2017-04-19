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

    wirelessSections = list()
    devices.readHostconfigWifi(wifi, wirelessSections)

    assert len(wirelessSections) == 1
    config, options = wirelessSections[0]
    assert config['type'] == 'wifi-device'
    assert config['name'].startswith('wifi')

    wifi = [{
        "phy": "phy0",
        "channel": 6
    }]

    wirelessSections = list()
    devices.readHostconfigWifi(wifi, wirelessSections)

    assert len(wirelessSections) == 1
    config, options = wirelessSections[0]
    assert config['type'] == 'wifi-device'
    assert config['name'].startswith('wifi')


@patch("paradrop.core.config.devices.getWirelessPhyName")
def test_readHostconfigWifiInterfaces(getWirelessPhyName):
    wifiInterfaces = [{
        "device": "wifi000000000000",
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
    assert options['device'] == 'wifi000000000000'
