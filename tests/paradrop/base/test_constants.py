from paradrop.base import constants

def test_constants():
    assert hasattr(constants, 'DAEMON_FEATURES')
    assert hasattr(constants, 'RESERVED_CHUTE_NAME')
