import tempfile

from mock import MagicMock, patch
from nose.tools import assert_raises


def test_generateHostConfig():
    """
    Test paradrop.lib.config.hostconfig.generateHostConfig
    """
    from paradrop.lib.config.hostconfig import generateHostConfig

    devices = dict()
    devices['wan'] = [{'name': 'eth0'}]
    devices['lan'] = [{'name': 'eth1'}]
    devices['wifi'] = [{'name': 'wlan0'}]

    config = generateHostConfig(devices)
    assert config['wan']['interface'] == "eth0"
    assert config['lan']['interfaces'] == ["eth1"]
    assert config['wifi'][0]['interface'] == "wlan0"


@patch("paradrop.lib.config.hostconfig.settings")
def test_loadHostConfig(settings):
    """
    Test paradrop.lib.config.hostconfig.loadHostConfig
    """
    from paradrop.lib.config.hostconfig import loadHostConfig

    devices = {
        'wan': [{'name': 'eth0'}],
        'lan': list(),
        'wifi': list()
    }

    source = tempfile.NamedTemporaryFile(delete=True)
    source.write("{test: value}")
    source.flush()

    settings.HOST_CONFIG_PATH = source.name

    config = loadHostConfig(devices)
    assert config['test'] == 'value'

    with patch("paradrop.lib.config.hostconfig.yaml") as yaml:
        yaml.load.side_effect = IOError()
        yaml.dump.return_value = "{test: value}"

        config = loadHostConfig(devices)
        assert config['wan']['interface'] == 'eth0'

        # Now simulate failure to write to file.
        # It should still return a config object.
        yaml.dump.side_effect = IOError()
        config = loadHostConfig(devices)
        assert config['wan']['interface'] == 'eth0'


@patch("paradrop.lib.config.hostconfig.loadHostConfig")
def test_getHostconfig(loadHostConfig):
    """
    Test paradrop.lib.config.hostconfig.getHostConfig
    """
    from paradrop.lib.config.hostconfig import getHostConfig

    update = MagicMock()
    getHostConfig(update)
    assert update.new.setCache.called
