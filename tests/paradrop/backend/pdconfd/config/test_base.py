from paradrop.backend.pdconfd.config import base
from mock import MagicMock

def test_base():
    m = MagicMock()
    assert base.ConfigObject().update(m, m) == None
