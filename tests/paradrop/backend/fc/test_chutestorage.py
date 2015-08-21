from paradrop.backend.fc import chutestorage
from mock import patch, MagicMock

@patch('paradrop.backend.fc.chutestorage.Chute')
@patch('paradrop.lib.utils.storage.PDStorage.saveToDisk')
def test_chutestorage(mSave, mChute):
    s = chutestorage.ChuteStorage()
    assert s.chuteList == {}
    s.setAttr('test')
    assert s.chuteList == 'test'
    s.setAttr({1: 'ch1', 2: 'ch2', 3: 'ch3'})
    for ch in ['ch1', 'ch2', 'ch3']:
        assert ch in s.getChuteList()
    #TODO: Finish Tests
