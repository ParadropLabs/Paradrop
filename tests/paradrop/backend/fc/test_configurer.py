from paradrop.backend.fc import configurer
from mock import patch, MagicMock

@patch('paradrop.backend.fc.configurer.out')
@patch('paradrop.backend.fc.configurer.updateObject')
@patch('paradrop.backend.fc.configurer.reloadChutes')
def test_Configurer(mReload, mUpdObj, mOut):

    storage = MagicMock()
    reactor = MagicMock()
    c = configurer.PDConfigurer(storage, reactor)
    reactor.callInThread.assert_called_once_with(c.performUpdates)
    #Test getNextUpdate & updateList & clearUpdateList
    assert c.updateQueue == []
    assert c.getNextUpdate() == None
    update1 = dict(update='test1')
    c.updateList(**update1)
    update2 = dict(update='test2')
    c.updateList(**update2)
    ret = c.getNextUpdate()
    assert  ret == update1
    assert update2 in c.updateQueue
    c.clearUpdateList()
    assert c.updateQueue == []

    #Test performUpdates
    reactor.running = True
    update = MagicMock()
    mUpdObj.parse.side_effect = [update, update, Exception('Bang!')]
    mOut.exception.side_effect = [Exception('Super-Bang!')]
    mReload.return_value = ['ch1', None, 'ch2', 'ch3']
    try:
        c.performUpdates()
    except Exception as e:
        assert e.message == 'Super-Bang!'
    assert mUpdObj.parse.call_count == 3
    assert update.execute.call_count == 2
