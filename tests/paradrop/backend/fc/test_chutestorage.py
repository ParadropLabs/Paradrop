from paradrop.backend.fc import chutestorage
from mock import patch, MagicMock
from paradrop.lib.chute import Chute
from paradrop.lib import settings 

@patch('paradrop.backend.fc.chutestorage.pdos')
@patch('paradrop.lib.utils.storage.PDStorage.saveToDisk')
def test_chutestorage(mSave, mPdos):

    #Test setAttr & getAttr
    s = chutestorage.ChuteStorage()
    assert s.chuteList == {}
    s.setAttr('test')
    assert s.chuteList == 'test'
    ch2 = MagicMock()
    s.setAttr({1: 'ch1', 2: ch2 , 3: 'ch3'})
    for ch in ['ch1', ch2, 'ch3']:
        assert ch in s.getChuteList()
    assert s.getAttr() == {1: 'ch1', 2: ch2, 3: 'ch3'}
    assert s.attrSaveable()

    #Test saveChute
    ch = MagicMock()
    ch.name = 'ch1'
    s.saveChute(ch)
    mSave.assert_called_once_with()
    mSave.reset_mock()
    ch.name = 2
    s.saveChute(ch)
    mSave.assert_called_once_with()

    #Test deleteChute
    ch = Chute({})
    assert not ch.isValid()
    mSave.reset_mock()
    ch.name = 'test'
    s.saveChute(ch)
    mSave.assert_called_once_with()
    assert ch in s.getChuteList()
    mSave.reset_mock()
    s.deleteChute(ch)
    mSave.assert_called_once_with()
    assert ch not in s.getChuteList()
    mSave.assert_called_once_with()
    assert 'ch1' in s.getChuteList()
    mSave.reset_mock()
    s.deleteChute(1)
    mSave.assert_called_once_with()
    assert 'ch1' not in s.getChuteList()

    #Test clearChuteStorage
    assert not mPdos.remove.called
    assert s.getChuteList != []
    s.clearChuteStorage()
    mPdos.remove.assert_called_once_with(settings.FC_CHUTESTORAGE_SAVE_PATH)
    assert s.getChuteList() == []

    

    #TODO: Finish Tests
