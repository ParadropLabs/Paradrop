from mock import patch, MagicMock

from paradrop.lib import resources


@patch("paradrop.lib.resources.getWirelessPhyName")
@patch("paradrop.lib.resources.prepareHostConfig")
@patch("paradrop.lib.resources.ChuteStorage")
def test_getDeviceReservations(ChuteStorage, prepareHostConfig, getWirelessPhyName):
    chute1 = MagicMock()
    chute1.getCache.return_value = [{
        'device': 'wlan0',
        'netType': 'wifi',
        'mode': 'ap'
    }]

    ChuteStorage.chuteList = {
        'chute1': chute1
    }

    # First test with no hostconfig interfaces.
    prepareHostConfig.return_value = {}

    reservations = resources.getDeviceReservations()
    assert reservations['wlan0'].count() == 1
    assert reservations['wlan0'].count(dtype="wifi") == 1
    assert reservations['wlan0'].count(mode="ap") == 1
    assert reservations['wlan0'].count(mode="monitor") == 0
    assert reservations['wlan1'].count() == 0

    prepareHostConfig.return_value = {
        'wifi-interfaces': [{
            'device': 'wlan0',
            'ifname': 'wlan0',
            'mode': 'ap',
            'ssid': 'paradrop',
            'network': 'lan'
        }]
    }

    getWirelessPhyName.side_effect = lambda x: x

    reservations = resources.getDeviceReservations()
    assert reservations['wlan0'].count() == 2
    assert reservations['wlan0'].count(dtype="wifi") == 2
    assert reservations['wlan0'].count(mode="ap") == 2
    assert reservations['wlan0'].count(mode="monitor") == 0
    assert reservations['wlan1'].count() == 0
