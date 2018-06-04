from paradrop.core.chute import restart
from paradrop.core.chute.chute import Chute
from paradrop.core.chute.chute_storage import ChuteStorage
from mock import patch, MagicMock

@patch.object(ChuteStorage, 'saveChute')
def test_updateStatus(mock_saveChute):
    """
    Test that the updateStatus function does it's job.
    """
    update = MagicMock()
    update.old.state = 'running'
    update.old.warning = None
    update.result.get.return_value = True
    restart.updateStatus(update)
    assert update.old.state == 'running'
    assert update.old.warning == None
    assert not mock_saveChute.called
    update.result.get.return_value = False
    restart.updateStatus(update)

@patch('paradrop.core.chute.restart.timeint')
@patch('paradrop.core.chute.restart.out')
@patch('paradrop.core.chute.restart.time')
@patch('paradrop.core.chute.restart.waitSystemUp')
@patch('paradrop.core.chute.restart.reclaimNetworkResources')
@patch('paradrop.core.chute.restart.settings')
@patch.object(ChuteStorage, 'getChute')
@patch.object(ChuteStorage, 'getChuteList')
def test_reloadChutes(mock_getChuteList, getChute, mockSettings, mResources, mWait, mTime, mOut, mTimeint):
    """
    Test that the reloadChutes function does it's job.
    """
    #Test that if pdconfd isn't enabled we return an empty list
    mockSettings.PDCONFD_ENABLED = False

    #Call
    ret = restart.reloadChutes()

    #Assertions
    assert ret == []
    assert not mock_getChuteList.called

    #Test that if pdconfd is enabled we do our job
    mTimeint.return_value = 'Now'
    mockSettings.PDCONFD_ENABLED = True
    mockSettings.RESERVED_CHUTE = 'PDROP'
    ch1 = Chute(name="ch1", state="running")
    ch2 = Chute(name="ch2", state="stopped")
    ch3 = Chute(name="ch3", state="running")
    mock_getChuteList.return_value = [ch1, ch2, ch3]
    mWait.side_effect = [None, None, '[{"success": false, "comment": "PDROP"},{"success": false, "comment": "ch1"},{"success": false, "comment": "ch2"},{"success": true, "comment": "ch3"},{"success": true, "comment": "error"}]']

    chutes = {ch.name: ch for ch in [ch1, ch2, ch3]}
    def mock_getChute(name):
        return chutes.get(name, None)
    getChute.side_effect = mock_getChute

    #Call
    ret = restart.reloadChutes()

    #Assertions
    mResources.assert_called_with(ch3)
    print(mResources.call_count)
    assert mResources.call_count == 2
    assert mTime.sleep.call_count == 2
    assert mTime.sleep.called_with(1)
    assert mOut.warn.call_count == 2
    assert 'Failed to load a system config section' in str(mOut.warn.call_args_list[0])
    assert 'Failed to load config section for unrecognized chute: ch2' in str(mOut.warn.call_args_list[1])
    assert all(update.updateType == "restart" for update in ret)
    assert all(update.new.name in chutes for update in ret)
