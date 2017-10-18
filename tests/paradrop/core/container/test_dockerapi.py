from mock import call, patch, MagicMock
from nose.tools import assert_raises

from paradrop.base.exceptions import ChuteNotFound
from paradrop.core.container import dockerapi


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
    chute.getWebPort.return_value = None
    assert dockerapi.getPortList(chute) == []

    chute.getWebPort.return_value = 80
    result = dockerapi.getPortList(chute)
    assert (80, 'tcp') in result

    chute.host_config = {
        'port_bindings': {
            "1111/udp": 1111,
            "2222": 2222
        }
    }

    result = dockerapi.getPortList(chute)
    assert (1111, 'udp') in result
    assert (2222, 'tcp') in result


@patch('paradrop.core.container.downloader.downloader')
@patch('paradrop.core.container.dockerapi._pullImage')
@patch('paradrop.core.container.dockerapi._buildImage')
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
    del update.workdir
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

    res = dockerapi._buildImage(update, client, True)
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


@patch('paradrop.base.nexus.core')
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

@patch('paradrop.core.container.dockerapi.subprocess')
@patch('paradrop.core.container.dockerapi.ChuteContainer.getPID')
@patch('paradrop.core.container.dockerapi.call_in_netns')
@patch('paradrop.core.container.dockerapi.call_retry')
def test_setup_net_interfaces(call_retry, call_in_netns, getPID, subprocess):
    chute = MagicMock()
    chute.name = 'test'
    chute.getCache.return_value = [{
        'netType': 'wifi',
        'ipaddrWithPrefix': '0.0.0.0/24',
        'internalIntf': 'Inside',
        'externalIntf': 'Outside',
        'phy': 'phy0'
    }, {
        'netType': 'wifi',
        'mode': 'monitor',
        'internalIntf': 'Inside',
        'externalIntf': 'Outside',
        'phy': 'phy1'
    }, {
        'netType': 'vlan',
        'ipaddrWithPrefix': '0.0.0.0/24',
        'internalIntf': 'Inside',
        'externalIntf': 'Outside'
    }]

    dockerapi.setup_net_interfaces(chute)

    assert getPID.called
    assert call_in_netns.called
    assert call_retry.called


@patch("paradrop.core.container.dockerapi.ChuteContainer")
def test_prepare_port_bindings(ChuteContainer):
    chute = MagicMock()
    chute.getHostConfig.return_value = {}
    chute.getWebPort.return_value = 80

    container = MagicMock()
    container.inspect.side_effect = ChuteNotFound()
    ChuteContainer.return_value = container

    bindings = dockerapi.prepare_port_bindings(chute)
    assert bindings["80/tcp"] is None

    container.inspect.side_effect = None
    container.inspect.return_value = {
        "NetworkSettings": {
            "Ports": {
                "80/tcp": [{
                    "HostIp": "0.0.0.0",
                    "HostPort": "32784"
                }]
            }
        }
    }

    bindings = dockerapi.prepare_port_bindings(chute)
    assert bindings["80/tcp"] == "32784"
