from nose.tools import assert_raises
from mock import mock_open, patch, MagicMock

from paradrop.core.config import airshark


@patch('paradrop.core.config.airshark.os.listdir')
def test_findInterfaceFromMAC(listdir):
    mac = '00:11:22:33:44:55'
    assert airshark.findInterfaceFromMAC(mac) is None

    listdir.return_value = ['wlan0']

    mopen = mock_open(read_data=mac)
    with patch('paradrop.core.config.airshark.open', mopen) as mock_file:
        assert airshark.findInterfaceFromMAC(mac) == 'wlan0'


@patch('paradrop.core.config.airshark.os.kill')
@patch('paradrop.core.config.airshark.subprocess.Popen')
def test_AirsharkManager(Popen, kill):
    manager = airshark.AirsharkManager()

    # Should return a list even if there is nothing.
    interfaces = manager.getActiveInterfaces()
    assert isinstance(interfaces, list)

    # Should be a path to a file that ends with '.pid'.
    pidPath = manager.getPidPath('wlan0')
    assert pidPath.endswith('wlan0.pid')

    # Test starting Airshark on a new interface.
    with patch.object(manager, 'start') as start:
        manager.setActive(['wlan0'])
        start.assert_called_with('wlan0')

    # Test stopping Airshark on one interface.
    with patch.object(manager, 'getActiveInterfaces') as getActiveInterfaces:
        getActiveInterfaces.return_value = ['wlan0', 'wlan1']
        with patch.object(manager, 'stop') as stop:
            manager.setActive(['wlan1'])
            stop.assert_called_with('wlan0')

    proc = MagicMock()
    proc.pid = 10000
    Popen.return_value = proc

    with patch.object(manager, 'getPidPath') as getPidPath:
        getPidPath.return_value = '/tmp/airshark.pid'

        manager.start('wlan0')
        assert Popen.called

        manager.stop('wlan0')
        assert kill.called


@patch('paradrop.core.config.airshark.AirsharkManager')
@patch('paradrop.core.config.airshark.findInterfaceFromMAC')
@patch('paradrop.core.config.airshark.airsharkInstalled')
def test_configure(airsharkInstalled, findInterfaceFromMAC, AirsharkManager):
    hostconfig = {
        'wifi-interfaces': [{
            'mode': 'ap',
            'device': '00:00:00:00:00:00'
        }, {
            'mode': 'airshark',
            'device': '00:00:00:00:00:01'
        }]
    }

    update = MagicMock()
    update.new.getCache.return_value = hostconfig

    findInterfaceFromMAC.return_value = 'wlan0'

    manager = MagicMock()
    AirsharkManager.return_value = manager

    # Pretend Airshark is installed.
    airsharkInstalled.return_value = True

    airshark.configure(update)
    manager.setActive.assert_called_with(['wlan0'])
