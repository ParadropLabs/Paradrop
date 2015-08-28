from mock import MagicMock, Mock, patch


@patch("os.remove")
@patch("socket.socket")
def test_CommandServer(socket, remove):
    """
    Test the CommandServer class
    """
    from pdinstall.server import CommandServer

    handler = MagicMock()

    server = CommandServer("/fake/path")
    server.addHandler("install", handler)
    assert "install" in server.handlers

    sock = MagicMock()
    socket.return_value = sock

    conn = MagicMock()
    sock.accept = Mock(return_value=(conn, Mock()))
    conn.recv.return_value = '{"command": "install"}'

    # Server should call conn.close no matter what.  We override that with a
    # function that end the main loop, so that our test does not run forever.
    def stopMainLoop():
        server.running = False
    conn.close = stopMainLoop

    server.run()

    assert sock.bind.called
    assert sock.listen.called
    assert handler.called
    remove.assert_called_with("/fake/path")
