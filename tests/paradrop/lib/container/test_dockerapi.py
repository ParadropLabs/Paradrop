from paradrop.lib.container import dockerapi
from mock import call, patch, MagicMock
from nose.tools import assert_raises


def test_getImageName():
    chute = MagicMock()
    chute.name = "test"
    chute.version = 1
    chute.external_image = "registry.exis.io/test:2"

    result = dockerapi.getImageName(chute)
    assert result == chute.external_image

    del chute.external_image
    result = dockerapi.getImageName(chute)
    assert result == "test:1"

    # For compatibility with older behavior, this should return name:latest
    # when version is not defined.
    del chute.version
    result = dockerapi.getImageName(chute)
    assert result == "test:latest"


def test_getPortList():
    chute = MagicMock()

    # Test with missing host_config.
    chute.host_config = None
    assert dockerapi.getPortList(chute) == []

    chute.host_config = {
        'port_bindings': {
            "1111/udp": 1111,
            "2222": 2222
        }
    }

    result = dockerapi.getPortList(chute)
    assert (1111, 'udp') in result
    assert 2222 in result


@patch('paradrop.lib.container.downloader.downloader')
@patch('paradrop.lib.container.dockerapi._pullImage')
@patch('paradrop.lib.container.dockerapi._buildImage')
@patch('docker.Client')
def test_buildImage(Client, _buildImage, _pullImage, downloader):
    client = MagicMock()
    Client.return_value = client

    _buildImage.return_value = True
    _pullImage.return_value = False

    downloader.return_value = MagicMock()

    update = MagicMock()
    del update.download

    # Test with dockerfile set.
    update.dockerfile = MagicMock()
    dockerapi.buildImage(update)
    _buildImage.assert_called_once()

    # Test with neither dockerfile nor download.
    del update.dockerfile
    assert_raises(Exception, dockerapi.buildImage, update)

    # Test where build worker function fails.
    update = MagicMock()
    _buildImage.return_value = False
    assert_raises(Exception, dockerapi.buildImage, update)


def test_buildImage_worker():
    update = MagicMock()
    client = MagicMock()

    client.build.return_value = [
        '{"message": "Message1"}',
        '{"message": "[===>      ] FOO"}',
        '{"message": "Message3   "}'
    ]

    res = dockerapi._buildImage(update, client)
    assert res is True

    # The second message should be suppressed as well as the whitespace after Message3.
    update.progress.assert_has_calls([call("Message1"), call("Message3")])


@patch('docker.Client')
def test_removeImage_worker(Client):
    client = MagicMock()
    Client.return_value = client

    chute = MagicMock()
    chute.name = "test"
    chute.version = 1

    dockerapi._removeImage(chute)
    assert client.remove_image.called_once_with(image="test:1")

    # Current behavior is to eat the exception, so this call should not raise
    # anything.
    client.remove_image.side_effect = Exception("Image does not exist.")
    dockerapi._removeImage(chute)


@patch('paradrop.base.lib.nexus.core')
def test_prepare_environment(core):
    chute = MagicMock()
    chute.name = "test"
    chute.version = 5
    chute.environment = {'CUSTOM_VARIABLE': 42}

    core.info.pdid = 'halo42'

    env = dockerapi.prepare_environment(chute)
    assert env['PARADROP_CHUTE_NAME'] == chute.name
    assert env['PARADROP_CHUTE_VERSION'] == chute.version
    assert env['PARADROP_ROUTER_ID'] == core.info.pdid
    assert env['CUSTOM_VARIABLE'] == 42
