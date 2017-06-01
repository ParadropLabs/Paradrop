from nose.tools import assert_raises
from mock import mock_open, patch, MagicMock

from paradrop.core.chute.chute import Chute
from paradrop.core.config import airshark

@patch("os.system")
def test_configure_airshark_enabled(mockSystem):
    hostconfig = {
        'wifi-interfaces': [{
            'mode': 'ap',
            'device': 'pci-wifi-0'
        }, {
            'mode': 'airshark',
            'device': 'usb-wifi-0'
        }]
    }

    networkDevices = {
        'wifi': [{
            'id': 'pci-wifi-0',
            'name': 'wifiXXXX',
            'mac': '00:00:00:00:00:01',
            'phy': 'phy0',
            'primary_interface': 'wlan0'
        }, {
            'id': 'usb-wifi-0',
            'name': 'wifiYYYY',
            'mac': '00:00:00:00:00:02',
            'phy': 'phy1',
            'primary_interface': 'wlan1'
        }]
    }

    update = MagicMock()
    update.new = Chute({})

    update.new.setCache('hostConfig', hostconfig)
    update.new.setCache('networkDevices', networkDevices)

    airshark.configure(update)
    mockSystem.assert_called()

@patch("os.system")
def test_configure_airshark_disabled(mockSystem):
    hostconfig = {
        'wifi-interfaces': [{
            'mode': 'ap',
            'device': 'pci-wifi-0'
        }, {
            'mode': 'ap',
            'device': 'usb-wifi-0'
        }]
    }

    networkDevices = {
        'wifi': [{
            'id': 'pci-wifi-0',
            'name': 'wifiXXXX',
            'mac': '00:00:00:00:00:01',
            'phy': 'phy0',
            'primary_interface': 'wlan0'
        }, {
            'id': 'usb-wifi-0',
            'name': 'wifiYYYY',
            'mac': '00:00:00:00:00:02',
            'phy': 'phy1',
            'primary_interface': 'wlan1'
        }]
    }

    update = MagicMock()
    update.new = Chute({})

    update.new.setCache('hostConfig', hostconfig)
    update.new.setCache('networkDevices', networkDevices)

    airshark.configure(update)
    mockSystem.assert_not_called()

@patch("os.system")
def test_configure_airshark_abnormal(mockSystem):
    hostconfig = {
        'wifi-interfaces': [{
            'mode': 'airshark',
            'device': 'pci-wifi-0'
        }, {
            'mode': 'airshark',
            'device': 'usb-wifi-0'
        }]
    }

    networkDevices = {
        'wifi': [{
            'id': 'pci-wifi-0',
            'name': 'wifiXXXX',
            'mac': '00:00:00:00:00:01',
            'phy': 'phy0',
            'primary_interface': 'wlan0'
        }, {
            'id': 'usb-wifi-0',
            'name': 'wifiYYYY',
            'mac': '00:00:00:00:00:02',
            'phy': 'phy1',
            'primary_interface': 'wlan1'
        }]
    }

    update = MagicMock()
    update.new = Chute({})

    update.new.setCache('hostConfig', hostconfig)
    update.new.setCache('networkDevices', networkDevices)

    assert_raises(Exception, airshark.configure, update)
    mockSystem.assert_not_called()
