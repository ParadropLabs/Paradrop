from mock import call, patch, MagicMock
from nose.tools import assert_raises

from paradrop.core.container import chutecontainer


@patch("paradrop.core.container.chutecontainer.ChuteContainer.inspect")
def test_getters(inspect):
    sample = {
        'Id': '01234567',
        'State': {
            'Pid': 1000,
            'Running': True,
            'Status': 'running'
        },
        'NetworkSettings': {
            'IPAddress': '172.',
            'Ports': {
                '80/tcp': [{
                    'HostIp': '0.0.0.0',
                    'HostPort': '32768'
                }]
            }
        }
    }
    inspect.return_value = sample

    container = chutecontainer.ChuteContainer("test")
    assert container.getID() == sample['Id']
    assert container.getIP() == sample['NetworkSettings']['IPAddress']
    assert container.getPID() == sample['State']['Pid']
    assert len(container.getPortConfiguration(80)) > 0
    assert container.getStatus() == sample['State']['Status']
    assert container.isRunning()

    sample['State']['Running'] = False
    sample['State']['Status'] = 'exited'
    assert_raises(Exception, container.getIP)
    assert_raises(Exception, container.getPID)
    assert container.isRunning() is False
