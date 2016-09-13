from paradrop.lib.container import dockerapi
from mock import call, patch, MagicMock
from nose.tools import assert_raises


def test_getImageName():
    chute = MagicMock()
    chute.name = "test"
    chute.version = 1

    result = dockerapi.getImageName(chute)
    assert result == "test:1"

    # For compatibility with older behavior, this should return name:latest
    # when version is not defined.
    del chute.version
    result = dockerapi.getImageName(chute)
    assert result == "test:latest"


@patch('paradrop.lib.container.downloader.downloader')
@patch('paradrop.lib.container.dockerapi._buildImage')
@patch('docker.Client')
def test_buildImage(Client, _buildImage, downloader):
    client = MagicMock()
    Client.return_value = client

    _buildImage.return_value = True

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


@patch('pdtools.lib.nexus.core')
def test_prepare_environment(core):
    chute = MagicMock()
    chute.name = "test"
    chute.version = 5

    core.info.pdid = 'halo42'

    env = dockerapi.prepare_environment(chute)
    assert env['PARADROP_CHUTE_NAME'] == chute.name
    assert env['PARADROP_CHUTE_VERSION'] == chute.version
    assert env['PARADROP_ROUTER_ID'] == core.info.pdid
