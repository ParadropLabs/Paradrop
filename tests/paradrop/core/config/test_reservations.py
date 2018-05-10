import ipaddress

from mock import patch, MagicMock

from paradrop.core.config import reservations


@patch("paradrop.core.config.reservations.getWirelessPhyName")
@patch("paradrop.core.config.reservations.prepareHostConfig")
@patch("paradrop.core.config.reservations.ChuteStorage")
def test_getDeviceReservations(ChuteStorage, prepareHostConfig, getWirelessPhyName):
    chute1 = MagicMock()
    chute1.getCache.return_value = [{
        'device': 'wlan0',
        'type': 'wifi',
        'mode': 'ap'
    }]

    ChuteStorage.chuteList = {
        'chute1': chute1
    }

    # First test with no hostconfig interfaces.
    prepareHostConfig.return_value = {}

    resv = reservations.getDeviceReservations()
    assert resv['wlan0'].count() == 1
    assert resv['wlan0'].count(dtype="wifi") == 1
    assert resv['wlan0'].count(mode="ap") == 1
    assert resv['wlan0'].count(mode="monitor") == 0
    assert resv['wlan1'].count() == 0

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

    resv = reservations.getDeviceReservations()
    assert resv['wlan0'].count() == 2
    assert resv['wlan0'].count(dtype="wifi") == 2
    assert resv['wlan0'].count(mode="ap") == 2
    assert resv['wlan0'].count(mode="monitor") == 0
    assert resv['wlan1'].count() == 0


@patch("paradrop.core.config.reservations.getWirelessPhyName")
@patch("paradrop.core.config.reservations.prepareHostConfig")
@patch("paradrop.core.config.reservations.ChuteStorage")
def test_getInterfaceReservations(ChuteStorage, prepareHostConfig, getWirelessPhyName):
    chute1 = MagicMock()
    chute1.getCache.return_value = [{
        'device': 'wlan0',
        'type': 'wifi',
        'mode': 'ap',
        'externalIntf': 'vwlan0.0000'
    }]

    ChuteStorage.chuteList = {
        'chute1': chute1
    }

    # First test with no hostconfig interfaces.
    prepareHostConfig.return_value = {}

    resv = reservations.getInterfaceReservations()
    assert 'vwlan0.0000' in resv

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

    resv = reservations.getInterfaceReservations()
    assert 'vwlan0.0000' in resv
    assert 'wlan0' in resv


def test_SubnetReservationSet():
    resv = reservations.SubnetReservationSet()
    assert len(resv) == 0

    net = ipaddress.ip_network(u'10.0.0.0/8')
    resv.add(net)
    assert len(resv) == 1
    assert net in resv

    # Overlapping, __contains__ should return True.
    netA = ipaddress.ip_network(u'10.10.10.0/24')
    assert netA in resv

    # Non-overlapping, __contains__ should return False.
    netB = ipaddress.ip_network(u'192.168.0.0/16')
    assert netB not in resv


@patch("paradrop.core.config.reservations.getWirelessPhyName")
@patch("paradrop.core.config.reservations.prepareHostConfig")
@patch("paradrop.core.config.reservations.ChuteStorage")
def test_getSubnetReservations(ChuteStorage, prepareHostConfig, getWirelessPhyName):
    chute1 = MagicMock()
    chute1.getCache.return_value = [{
        'device': 'wlan0',
        'type': 'wifi',
        'mode': 'ap',
        'externalIntf': 'vwlan0.0000',
        'subnet': MagicMock()
    }]

    ChuteStorage.chuteList = {
        'chute1': chute1
    }

    # First test with no hostconfig interfaces.
    prepareHostConfig.return_value = {}

    resv = reservations.getSubnetReservations()
    assert len(resv) == 1
