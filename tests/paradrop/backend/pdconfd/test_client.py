from paradrop.backend.pdconfd import client
from txdbus import error
from mock import MagicMock, patch

@patch('paradrop.backend.pdconfd.client.out')
@patch('paradrop.backend.pdconfd.client.defer')
@patch('paradrop.backend.pdconfd.client.client')
def test_client(mClient, mDefer, mOut):
    e = error.DBusException('Test')
    conn = MagicMock()
    robj = MagicMock()
    mClient.connect.return_value = conn
    conn.getRemoteObject.return_value = robj
    robj.callRemote.return_value = 'testing'
    mDefer.returnValue.side_effect = e
    client.callDeferredMethod('test', *{})
    mDefer.returnValue.assert_called_once_with('testing')
    mOut.err.assert_called_once_with("D-Bus error: {}" .format(e))

@patch('paradrop.backend.pdconfd.client.threading')
def test_Blocking(mThread):
    deffered = MagicMock()
    mThread.Event.return_value = MagicMock()
    block = client.Blocking(deffered)
    mThread.Event.assert_called_once_with()
    deffered.addCallback.assert_called_once_with(block.unlock)
    block.unlock('test')
    assert block.result == 'test'
    mes = 'test'
    mThread.currentThread.return_value = MagicMock()
    mThread.currentThread.return_value.getName.return_value = 'MainThread'
    try:
        block.wait()
    except Exception as e:
        mes = e.message
    print mes
    assert mes == "Blocking in reactor main thread"
    mThread.currentThread.return_value = MagicMock()
    mThread.currentThread.return_value.getName.return_value = 'OtherThread'
    assert block.wait() == 'test'
    mThread.Event.return_value.wait.assert_called_once_with()

@patch('paradrop.backend.pdconfd.client.callDeferredMethod')
@patch('paradrop.backend.pdconfd.client.Blocking')
@patch('paradrop.backend.pdconfd.client.ConfigService')
def test_reloadAll(mConfig, mBlocking, mDeffered):
    mDeffered.return_value = 'test'
    mBlocking.return_value = MagicMock()
    mBlocking.return_value.wait.return_value = 'wait test'
    assert client.reloadAll(dbus=True) == 'wait test'
    mDeffered.assert_called_once_with('ReloadAll')
    mBlocking.assert_called_once_with('test')

    mConfig.configManager.loadConfig.return_value = "new test"
    assert client.reloadAll() == 'new test'

@patch('paradrop.backend.pdconfd.client.callDeferredMethod')
@patch('paradrop.backend.pdconfd.client.Blocking')
@patch('paradrop.backend.pdconfd.client.ConfigService')
def test_reload(mConfig, mBlocking, mDeffered):
    path = "path!"
    mDeffered.return_value = 'test'
    mBlocking.return_value = MagicMock()
    mBlocking.return_value.wait.return_value = 'wait test'
    assert client.reload(path, dbus=True) == 'wait test'
    mDeffered.assert_called_once_with('Reload', path)
    mBlocking.assert_called_once_with('test')

    mConfig.configManager.loadConfig.return_value = "new test"
    assert client.reload(path) == 'new test'
    mConfig.configManager.loadConfig.assert_called_once_with(path)

@patch('paradrop.backend.pdconfd.client.callDeferredMethod')
@patch('paradrop.backend.pdconfd.client.Blocking')
@patch('paradrop.backend.pdconfd.client.ConfigService')
def test_waitSystemUp(mConfig, mBlocking, mDeffered):
    mDeffered.return_value = 'test'
    mBlocking.return_value = MagicMock()
    mBlocking.return_value.wait.return_value = 'wait test'
    assert client.waitSystemUp(dbus=True) == 'wait test'
    mDeffered.assert_called_once_with('WaitSystemUp')
    mBlocking.assert_called_once_with('test')

    mConfig.configManager.waitSystemUp.return_value = "new test"
    assert client.waitSystemUp() == 'new test'
