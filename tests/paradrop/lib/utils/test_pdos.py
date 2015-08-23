from paradrop.lib.utils import pdos
from paradrop.lib.utils import pdosq
from mock import patch

@patch('paradrop.lib.utils.pdos.os')
def test_pdos(mOs):
    pdos.listdir('test')
    mOs.listdir.assert_called_once_with('test')

@patch('paradrop.lib.utils.pdosq.os')
def test_pdoqs(mOs):
    assert pdosq.makedirs('test')
    mOs.makedirs.assert_called_once_with('test')
