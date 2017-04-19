from paradrop.core.chute import restart
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
@patch.object(ChuteStorage, 'getChuteList')
def test_reloadChutes(mock_getChuteList, mockSettings, mResources, mWait, mTime, mOut, mTimeint):
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
    ch1 = MagicMock()
    ch2 = MagicMock()
    ch3 = MagicMock()
    ch1.state = 'running'
    ch1.name = 'ch1'
    ch2.state = 'stopped'
    ch3.state = 'running'
    ch3.name = 'ch3'
    mock_getChuteList.return_value = [ch1, ch2, ch3]
    mWait.side_effect = [None, None, '[{"success": false, "comment": "PDROP"},{"success": false, "comment": "ch1"},{"success": false, "comment": "ch2"},{"success": true, "comment": "ch3"},{"success": true, "comment": "error"}]']

    #Call
    ret = restart.reloadChutes()

    #Assertions
    mResources.assert_called_with(ch3)
    assert mResources.call_count == 2
    assert mTime.sleep.call_count == 2
    assert mTime.sleep.called_with(1)
    assert mOut.warn.call_count == 2
    assert 'Failed to load a system config section' in str(mOut.warn.call_args_list[0])
    assert 'Failed to load config section for unrecognized chute: ch2' in str(mOut.warn.call_args_list[1])
    assert dict(updateClass='CHUTE', updateType='restart', name=ch3.name, tok=mTimeint.return_value, func=restart.updateStatus) in ret
