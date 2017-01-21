from mock import patch, MagicMock

from paradrop.lib.misc import resources


@patch("paradrop.lib.misc.resources.getWirelessPhyName")
@patch("paradrop.lib.misc.resources.prepareHostConfig")
@patch("paradrop.lib.misc.resources.ChuteStorage")
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
        'aps': [{
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


@patch("paradrop.lib.misc.resources.getWirelessPhyName")
@patch("paradrop.lib.misc.resources.prepareHostConfig")
@patch("paradrop.lib.misc.resources.ChuteStorage")
def test_getInterfaceReservations(ChuteStorage, prepareHostConfig, getWirelessPhyName):
    chute1 = MagicMock()
    chute1.getCache.return_value = [{
        'device': 'wlan0',
        'netType': 'wifi',
        'mode': 'ap',
        'externalIntf': 'vwlan0.0000'
    }]

    ChuteStorage.chuteList = {
        'chute1': chute1
    }

    # First test with no hostconfig interfaces.
    prepareHostConfig.return_value = {}

    reservations = resources.getInterfaceReservations()
    assert 'vwlan0.0000' in reservations

    prepareHostConfig.return_value = {
        'aps': [{
            'device': 'wlan0',
            'ifname': 'wlan0',
            'mode': 'ap',
            'ssid': 'paradrop',
            'network': 'lan'
        }]
    }

    getWirelessPhyName.side_effect = lambda x: x

    reservations = resources.getInterfaceReservations()
    assert 'vwlan0.0000' in reservations
    assert 'wlan0' in reservations


@patch("paradrop.lib.misc.resources.getWirelessPhyName")
@patch("paradrop.lib.misc.resources.prepareHostConfig")
@patch("paradrop.lib.misc.resources.ChuteStorage")
def test_getSubnetReservations(ChuteStorage, prepareHostConfig, getWirelessPhyName):
    chute1 = MagicMock()
    chute1.getCache.return_value = [{
        'device': 'wlan0',
        'netType': 'wifi',
        'mode': 'ap',
        'externalIntf': 'vwlan0.0000',
        'subnet': MagicMock()
    }]

    ChuteStorage.chuteList = {
        'chute1': chute1
    }

    # First test with no hostconfig interfaces.
    prepareHostConfig.return_value = {}

    reservations = resources.getSubnetReservations()
    assert len(reservations) == 1
