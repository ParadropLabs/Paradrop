import tempfile

from mock import MagicMock, patch
from nose.tools import assert_raises


def test_generateHostConfig():
    """
    Test paradrop.core.config.hostconfig.generateHostConfig
    """
    from paradrop.core.config.hostconfig import generateHostConfig

    devices = dict()
    devices['wan'] = [{
        'name': 'eth0',
        'mac': '00:00:00:00:00:00',
        'ifname': 'eth0'
    }]
    devices['lan'] = [{
        'name': 'eth1',
        'mac': '00:00:00:00:00:01',
        'ifname': 'eth1'
    }]
    devices['wifi'] = [{
        'name': 'phy0',
        'mac': '00:00:00:00:00:02',
        'ifname': 'wlan0',
        'vendor': '16ic',
        'device': '002a',
        'id': 'pci-wifi-0'
    }]

    config = generateHostConfig(devices)
    assert config['wan']['interface'] == "eth0"
    assert config['lan']['interfaces'] == ["eth1"]
    assert config['wifi'][0]['id'] == "pci-wifi-0"


@patch("paradrop.core.config.devices.detectSystemDevices")
@patch("paradrop.core.config.hostconfig.settings")
def test_prepareHostConfig(settings, detectSystemDevices):
    """
    Test paradrop.core.config.hostconfig.prepareHostConfig
    """
    from paradrop.core.config.hostconfig import prepareHostConfig

    devices = {
        'wan': [{'name': 'eth0'}],
        'lan': list(),
        'wifi': list()
    }
    detectSystemDevices.return_value = devices

    source = tempfile.NamedTemporaryFile(delete=True)
    source.write("{test: value}")
    source.flush()

    settings.HOST_CONFIG_FILE = source.name
    settings.DEFAULT_LAN_ADDRESS = "1.2.3.4"
    settings.DEFAULT_LAN_NETWORK = "1.0.0.0/24"

    config = prepareHostConfig()
    assert config['test'] == 'value'

    with patch("paradrop.core.config.hostconfig.yaml") as yaml:
        yaml.safe_load.side_effect = IOError()
        yaml.safe_dump.return_value = "{test: value}"

        config = prepareHostConfig()
        assert config['wan']['interface'] == 'eth0'
        assert config['lan']['ipaddr'] == "1.2.3.4"
        assert config['lan']['netmask'] == "255.255.255.0"

        # Now simulate failure to write to file.
        yaml.safe_dump.side_effect = IOError()
        assert_raises(Exception, prepareHostConfig)


@patch("paradrop.core.config.hostconfig.prepareHostConfig")
def test_getHostconfig(prepareHostConfig):
    """
    Test paradrop.core.config.hostconfig.getHostConfig
    """
    from paradrop.core.config.hostconfig import getHostConfig

    update = MagicMock()
    getHostConfig(update)
    assert update.cache_set.called


@patch("paradrop.core.config.hostconfig.prepareHostConfig")
def test_patchHostconfig(prepareHostConfig):
    from paradrop.core.config.hostconfig import getHostConfig

    update = MagicMock()
    update.updateType = "patchhostconfig"

    patch = [
        {"op": "replace", "path": "/zerotier/enabled", "value": True},
        {"op": "add", "path": "/zerotier/networks", "value": "e5cd7a9e1c2753e4"}
    ]

    getHostConfig(update)
    assert update.cache_set.called
