from paradrop.confd import client
from mock import MagicMock, patch

@patch('paradrop.confd.client_dbus.out')
@patch('paradrop.confd.client_dbus.defer')
@patch('paradrop.confd.client_dbus.client')
def test_client(mClient, mDefer, mOut):
    from txdbus import error
    e = error.DBusException('Test')
    conn = MagicMock()
    robj = MagicMock()
    mClient.connect.return_value = conn
    conn.getRemoteObject.return_value = robj
    robj.callRemote.return_value = 'testing'
    mDefer.returnValue.side_effect = e
    client.callDeferredMethodDbus('test', *{})
    mDefer.returnValue.assert_called_once_with('testing')
    mOut.err.assert_called_once_with("D-Bus error: {}" .format(e))

@patch('paradrop.confd.client_rpc.out')
@patch('paradrop.confd.client_rpc.defer')
@patch('paradrop.confd.client_rpc.client')
def test_client(mClient, mDefer, mOut):
    e = Exception('rpc error')
    conn = MagicMock()
    mClient.connect_UNIX.return_value = conn
    conn.createRequest.return_value = 'testing'
    mDefer.returnValue.side_effect = e
    client.callDeferredMethodRpc('test', *{})
    mDefer.returnValue.assert_called_once_with('testing')
    mOut.err.assert_called_once_with("Unix sockets error: {}" .format(e))

@patch('paradrop.confd.client.threading')
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

@patch('paradrop.confd.client.callDeferredMethodDbus')
@patch('paradrop.confd.client.Blocking')
@patch('paradrop.confd.client.configManager')
def test_reloadAll(mConfigManager, mBlocking, mDeffered):
    mDeffered.return_value = 'test'
    mBlocking.return_value = MagicMock()
    mBlocking.return_value.wait.return_value = 'wait test'
    assert client.reloadAll(adapter='dbus') == 'wait test'
    mDeffered.assert_called_once_with('ReloadAll')
    mBlocking.assert_called_once_with('test')

    mConfigManager.loadConfig.return_value = "new test"
    assert client.reloadAll() == 'new test'

@patch('paradrop.confd.client.callDeferredMethodDbus')
@patch('paradrop.confd.client.Blocking')
@patch('paradrop.confd.client.configManager')
def test_reload(mConfigManager, mBlocking, mDeffered):
    path = "path!"
    mDeffered.return_value = 'test'
    mBlocking.return_value = MagicMock()
    mBlocking.return_value.wait.return_value = 'wait test'
    assert client.reload(path, adapter='dbus') == 'wait test'
    mDeffered.assert_called_once_with('Reload', path)
    mBlocking.assert_called_once_with('test')

    mConfigManager.loadConfig.return_value = "new test"
    assert client.reload(path) == 'new test'
    mConfigManager.loadConfig.assert_called_once_with(path)

@patch('paradrop.confd.client.callDeferredMethodDbus')
@patch('paradrop.confd.client.Blocking')
@patch('paradrop.confd.client.configManager')
def test_waitSystemUp(mConfigManager, mBlocking, mDeffered):
    mDeffered.return_value = 'test'
    mBlocking.return_value = MagicMock()
    mBlocking.return_value.wait.return_value = 'wait test'
    assert client.waitSystemUp(adapter='dbus') == 'wait test'
    mDeffered.assert_called_once_with('WaitSystemUp')
    mBlocking.assert_called_once_with('test')

    mConfigManager.waitSystemUp.return_value = "new test"
    assert client.waitSystemUp() == 'new test'
