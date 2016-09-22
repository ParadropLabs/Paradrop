from nose.tools import assert_raises
from mock import MagicMock, Mock, patch

from paradrop.lib.config import network


def test_getInterfaceDict():
    # getInterfaceDict should be able to handle null chute.
    assert network.getInterfaceDict(None) == {}

    chute = MagicMock()
    chute.getCache.return_value = []
    assert network.getInterfaceDict(chute) == {}

    chute = MagicMock()
    chute.getCache.return_value = [
        {'name': 'eth0'},
        {'name': 'eth1'}
    ]
    ifaces = network.getInterfaceDict(chute)
    assert 'eth0' in ifaces
    assert 'eth1' in ifaces
