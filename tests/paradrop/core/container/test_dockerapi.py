from mock import call, patch, MagicMock
from nose.tools import assert_raises

from paradrop.base.exceptions import ChuteNotFound
from paradrop.core.container import dockerapi
from paradrop.core.chute.chute import Chute
from paradrop.core.chute.service import Service


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
@patch('paradrop.core.container.dockerapi._pull_image')
@patch('paradrop.core.container.dockerapi._build_image')
@patch('paradrop.core.container.dockerapi.settings')
@patch('docker.APIClient')
def test_prepare_image(Client, settings, _build_image, _pull_image, downloader):
    client = MagicMock()
    Client.return_value = client

    _build_image.return_value = True
    _pull_image.return_value = False

    downloader.return_value = MagicMock()

    service = MagicMock()

    update = MagicMock()
    del update.download

    # Disable concurrent builds so that prepare_image calls _build_image
    # directly, rather than trying to push it off to a worker thread.
    settings.CONCURRENT_BUILDS = False

    # Test with dockerfile set.
    update.dockerfile = MagicMock()
    dockerapi.prepare_image(update, service)
    _build_image.assert_called_once()

    # Test with neither dockerfile nor download.
    del update.dockerfile
    del update.workdir
    assert_raises(Exception, dockerapi.prepare_image, update, service)


def test_buildImage_worker():
    update = MagicMock()
    service = MagicMock()
    client = MagicMock()

    client.build.return_value = [
        '{"message": "Message1"}',
        '{"message": "[===>      ] FOO"}',
        '{"message": "Message3   "}'
    ]

    res = dockerapi._build_image(update, service, client, True)
    assert res is None

    # The second message should be suppressed as well as the whitespace after Message3.
    update.progress.assert_has_calls([call("Message1"), call("Message3")])


@patch('docker.APIClient')
def test_remove_image(Client):
    client = MagicMock()
    Client.return_value = client

    update = MagicMock()
    service = MagicMock()

    dockerapi.remove_image(update, service)
    assert client.remove_image.called_once_with(image="test:1")

    # Current behavior is to eat the exception, so this call should not raise
    # anything.
    client.remove_image.side_effect = Exception("Image does not exist.")
    dockerapi.remove_image(update, service)


@patch('paradrop.base.nexus.core')
def test_prepare_environment(core):
    chute = MagicMock()
    chute.name = "test"
    chute.version = 5

    core.info.pdid = 'halo42'

    update = MagicMock()
    update.new = chute

    service = MagicMock()
    service.environment = {"CUSTOM_VARIABLE": 42}

    env = dockerapi.prepare_environment(update, service)
    assert env['PARADROP_CHUTE_NAME'] == chute.name
    assert env['PARADROP_CHUTE_VERSION'] == chute.version
    assert env['PARADROP_ROUTER_ID'] == core.info.pdid
    assert env['CUSTOM_VARIABLE'] == 42

@patch('paradrop.core.container.dockerapi.subprocess')
@patch('paradrop.core.container.dockerapi.ChuteContainer.getPID')
@patch('paradrop.core.container.dockerapi.call_in_netns')
@patch('paradrop.core.container.dockerapi.call_retry')
def test_setup_net_interfaces(call_retry, call_in_netns, getPID, subprocess):
    update = MagicMock()
    update.cache_get.return_value = [{
        'service': 'main',
        'type': 'wifi',
        'ipaddrWithPrefix': '0.0.0.0/24',
        'internalIntf': 'Inside',
        'externalIntf': 'Outside',
        'phy': 'phy0'
    }, {
        'service': 'main',
        'type': 'wifi',
        'mode': 'monitor',
        'internalIntf': 'Inside',
        'externalIntf': 'Outside',
        'phy': 'phy1'
    }, {
        'service': 'main',
        'type': 'vlan',
        'ipaddrWithPrefix': '0.0.0.0/24',
        'internalIntf': 'Inside',
        'externalIntf': 'Outside'
    }]

    service = MagicMock()
    update.new.get_service.return_value = service

    dockerapi.setup_net_interfaces(update)

    assert getPID.called
    assert call_in_netns.called
    assert call_retry.called


@patch("paradrop.core.container.dockerapi.ChuteContainer")
def test_prepare_port_bindings(ChuteContainer):
    chute = Chute(name="test")
    chute.web = {
        "service": "main",
        "port": 80
    }

    service = Service(name="main")
    service.chute = chute
    chute.add_service(service)

    container = MagicMock()
    container.inspect.side_effect = ChuteNotFound()
    ChuteContainer.return_value = container

    bindings = dockerapi.prepare_port_bindings(service)
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

    bindings = dockerapi.prepare_port_bindings(service)
    assert bindings["80/tcp"] == "32784"
