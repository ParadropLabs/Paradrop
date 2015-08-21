from paradrop.lib.utils import restart
from mock import patch, MagicMock

@patch('paradrop.backend.fc.chutestorage.ChuteStorage')
def test_updateStatus(mockStore):
    """
    Test that the updateStatus function does it's job.
    """
    storage = MagicMock()
    mockStore.return_value = storage
    update = MagicMock()
    update.old.state = 'running'
    update.old.warning = None
    update.result.get.return_value = True
    restart.updateStatus(update)
    assert update.old.state == 'running'
    assert update.old.warning == None
    assert not storage.saveChute.called
    update.result.get.return_value = False
    restart.updateStatus(update)
    assert update.old.state == 'stopped'
    assert update.old.warning == restart.FAILURE_WARNING
    assert storage.saveChute.called

@patch('paradrop.lib.utils.restart.timeint')
@patch('paradrop.lib.utils.restart.out')
@patch('paradrop.lib.utils.restart.time')
@patch('paradrop.lib.utils.restart.waitSystemUp')
@patch('paradrop.lib.utils.restart.reclaimNetworkResources')
@patch('paradrop.lib.utils.restart.settings')
@patch('paradrop.backend.fc.chutestorage.ChuteStorage')
def test_reloadChutes(mockStore, mockSettings, mResources, mWait, mTime, mOut, mTimeint):
    """
    Test that the reloadChutes function does it's job.
    """
    #Test that if pdconfd isn't enabled we return an empty list
    mockSettings.PDCONFD_ENABLED = False
    storage = MagicMock()
    mockStore.return_value = storage

    #Call
    ret = restart.reloadChutes()

    #Assertions
    assert ret == []
    assert not mockStore.called

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
    storage.getChuteList.return_value = [ch1, ch2, ch3]
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
    assert dict(updateClass='CHUTE', updateType='stop', name=ch1.name, tok=mTimeint.return_value, func=restart.updateStatus, warning=restart.FAILURE_WARNING) in ret
    assert dict(updateClass='CHUTE', updateType='restart', name=ch3.name, tok=mTimeint.return_value, func=restart.updateStatus) in ret
