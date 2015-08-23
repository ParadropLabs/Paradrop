from paradrop.lib.utils import addresses
from mock import MagicMock

def test_addresses():
    ch = MagicMock()
    ch.getCache.return_value = [{'netType': 'test'}]
    assert addresses.getGatewayIntf(ch) == (None, None)
    assert addresses.getWANIntf(ch) == None
