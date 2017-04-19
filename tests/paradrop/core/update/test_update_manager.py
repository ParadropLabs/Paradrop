from paradrop.core.update import update_manager, update_object
from mock import patch, MagicMock

@patch('paradrop.core.update.update_manager.out')
@patch('paradrop.core.update.update_object')
@patch('paradrop.core.update.update_manager.reloadChutes')
def test_update_manager(mReload, mUpdObj, mOut):
    reactor = MagicMock()
    c = update_manager.UpdateManager(reactor)
    reactor.callInThread.assert_called_once_with(c._perform_updates)

    #Test getNextUpdate & updateList & clearUpdateList
    assert c.updateQueue == []
    assert c._get_next_update() == None
    update1 = dict(update='test1')
    c.add_update(**update1)
    update2 = dict(update='test2')
    c.add_update(**update2)
    ret = c._get_next_update()
    assert ret['update'] == 'test1'
    ret = c._get_next_update()
    assert ret['update'] == 'test2'
    c.clear_update_list()
    assert c.updateQueue == []

    #Test performUpdates
    #reactor.running = True
    #update = MagicMock()
    #mUpdObj.parse.side_effect = [update, update, Exception('Bang!')]
    #mOut.exception.side_effect = [Exception('Super-Bang!')]
    #mReload.return_value = ['ch1', None, 'ch2', 'ch3']
    #mMakeHostConfig.return_value = [update, update, update, update]
    #try:
    #    c._perform_updates(checkDocker=False)
    #except Exception as e:
    #    assert e.message == 'Super-Bang!'
    #assert mUpdObj.parse.call_count == 3
    #assert update.execute.call_count == 2

