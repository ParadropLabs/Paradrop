import time
from mock import patch, MagicMock

from paradrop.backend import token_manager


def test_generate_jwt_secret():
    secret = token_manager.generate_jwt_secret()
    assert isinstance(secret, basestring)
    assert len(secret) >= 32


@patch("paradrop.backend.token_manager.nexus")
def test_TokenManager_issue(nexus):
    nexus.core.info.pdid = 'halo42'
    nexus.core.getKey.return_value = None

    manager = token_manager.TokenManager()
    token = manager.issue('test')
    assert isinstance(token, basestring)

    decoded = manager.decode(token)
    assert decoded['exp'] > time.time()
    assert decoded['iat'] < time.time()
    assert decoded['iss'] == nexus.core.info.pdid
    assert decoded['sub'] == 'test'
