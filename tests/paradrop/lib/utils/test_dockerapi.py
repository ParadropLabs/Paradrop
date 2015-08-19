from paradrop.lib.utils import dockerapi
from mock import patch, MagicMock

HOST_CONFIG1 = {'RestartPolicy': {'MaximumRetryCount': 5, 'Name': 'on-failure'}, 'LxcConf': [], 'CapAdd': ['NET_ADMIN']}
HOST_CONFIG2 = {'RestartPolicy': {'MaximumRetryCount': 5, 'Name': 'on-failure'}, 'PortBindings': {'80/tcp': [{'HostPort': '9000', 'HostIp': ''}]}, 'LxcConf': [], 'Dns': ['0.0.0.0', '8.8.8.8'], 'CapAdd': ['NET_ADMIN']}

def fake_update():
    class Object(object):
        pass

    update = Object()
    update.new = Object()
    update.new.host_config = {}
    return update

def test_build_host_config():
    """
    Test that the build_host_config function does it's job.
    """
    #Check that an empty host_config gives us certain default settings
    u = fake_update()
    res = dockerapi.build_host_config(u)
    print 'Expected: ', HOST_CONFIG1, '\nResult: ', res, '\n'
    assert res == HOST_CONFIG1

    #Check that passing things through host_config works
    u.new.host_config = {'port_bindings': { 80:9000}, 'dns': ['0.0.0.0', '8.8.8.8']}
    res = dockerapi.build_host_config(u)
    print 'Expected: ', HOST_CONFIG2, '\nResult: ', res, '\n'
    assert res == HOST_CONFIG2

#mock the output module but no need to test
@patch('paradrop.lib.utils.dockerapi.out')
#Make sure we use mock docker client
@patch('docker.Client')
def test_failAndCleanUpDocker(mockDocker, mockOutput):
    """
    Test that the failure and clean up function does it's job.
    """
    client = MagicMock()
    mockDocker.return_value = client
    #call clean up with empty sets, matching sets, and different sets for valid and current images and test
    for pair in [[[],[]], [[1, 2, 3], [1, 2, 3]], [[{'Id': 1}, {'Id': 2}, {'Id': 3}], [{'Id': 1}, {'Id': 2}, {'Id': 3}, {'Id': 4}, {'Id': 5}]]]:
        #fake that docker is returning the second list in the pair as the current images and containers on the device
        client.containers.return_value = pair[1]
        client.images.return_value = pair[1]
        try:
            dockerapi.failAndCleanUpDocker(pair[0],pair[0])
        except Exception as e:
            #we should always see this exception
            assert e.message == 'Building or starting of docker image failed check your Dockerfile for errors.'
        mockDocker.assert_called_with(base_url='unix://var/run/docker.sock', version='auto')
        client.containers.assert_called_once_with(quiet=True, all=True)
        client.images.assert_called_once_with(quiet=True, all=False)
        if pair[1] == pair[0]:
            assert client.remove_image.call_count == 0
            assert client.remove_container.call_count == 0
        else:
            img_expected = "[call(image={'Id': 4}), call(image={'Id': 5})]"
            cntr_expected = "[call(container=4), call(container=5)]"
            assert str(client.remove_image.call_args_list) == img_expected
            assert str(client.remove_container.call_args_list) == cntr_expected
            assert client.remove_image.call_count == 2
            assert client.remove_container.call_count == 2
        client.reset_mock()

@patch('paradrop.lib.utils.dockerapi.setup_net_interfaces')
@patch('paradrop.lib.utils.dockerapi.out')
@patch('docker.Client')
def test_restartChute(mockDocker, mockOutput, mockInterfaces):
    """
    Test that the restartChute function does it's job.
    """
    update = MagicMock()
    update.name = 'test'
    client = MagicMock()
    mockDocker.return_value = client
    dockerapi.restartChute(update)
    mockDocker.assert_called_once_with(base_url='unix://var/run/docker.sock', version='auto')
    mockInterfaces.assert_called_once_with(update)
    client.start.assert_called_once_with(container=update.name)

@patch('paradrop.lib.utils.dockerapi.out')
@patch('docker.Client')
def test_stopChute(mockDocker, mockOutput):
    """
    Test that the stopChute function does it's job.
    """
    update = MagicMock()
    update.name = 'test'
    client = MagicMock()
    mockDocker.return_value = client
    dockerapi.stopChute(update)
    mockDocker.assert_called_once_with(base_url='unix://var/run/docker.sock', version='auto')
    client.stop.assert_called_once_with(container=update.name)

@patch('paradrop.lib.utils.dockerapi.out')
@patch('docker.Client')
def test_removeChute(mockDocker, mockOutput):
    """
    Test that the stopChute function does it's job.
    """
    update = MagicMock()
    update.name = 'test'
    client = MagicMock()
    mockDocker.return_value = client
    dockerapi.removeChute(update)
    mockDocker.assert_called_once_with(base_url='unix://var/run/docker.sock', version='auto')
    client.remove_container.assert_called_once_with(container=update.name, force=True)
    client.remove_image.assert_called_once_with(image='test:latest')
    assert update.complete.call_count == 0
    client.reset_mock()
    client.remove_container.side_effect = Exception('Test')
    try:
        dockerapi.removeChute(update)
    except Exception as e:
        print e.message
        assert e.message == 'Test'
    client.remove_container.assert_called_once_with(container=update.name, force=True)
    assert update.complete.call_count == 1

@patch('paradrop.lib.utils.dockerapi.failAndCleanUpDocker')
@patch('paradrop.lib.utils.dockerapi.build_host_config')
@patch('paradrop.lib.utils.dockerapi.setup_net_interfaces')
@patch('paradrop.lib.utils.dockerapi.out')
@patch('docker.Client')
def test_startChute(mockDocker, mockOutput, mockInterfaces, mockConfig, mockFail):
    """
    Test that the startChute function does it's job.
    """
    update = MagicMock()
    update.name = 'test'
    update.dockerfile = 'Dockerfile'
    client = MagicMock()
    client.images.return_value = 'images'
    client.containers.return_value = 'containers'
    mockDocker.return_value = client
    dockerapi.startChute(update)
    mockDocker.assert_called_once_with(base_url='unix://var/run/docker.sock', version='auto')
    mockConfig.assert_called_once_with(update)
    client.images.assert_called_once_with(quiet=True, all=False)
    client.containers.assert_called_once_with(quiet=True, all=True)
    mockInterfaces.assert_called_once_with(update)
    #TODO Finish unit testing this function
