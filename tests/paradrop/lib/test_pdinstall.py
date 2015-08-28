from mock import MagicMock, patch


@patch("socket.socket")
def test_sendCommand(socket):
    """
    Test paradrop.lib.pdinstall.sendCommand
    """
    from paradrop.lib.pdinstall import sendCommand

    command = "install"
    sources = ["paradrop_0.1.0_all.snap"]

    sock = MagicMock()
    socket.return_value = sock

    assert sendCommand(command, sources=sources)
    assert sock.connect.called
    assert sock.send.called
    assert sock.close.called

    sock.reset_mock
    sock.connect.side_effect = Exception("Boom!")

    assert sendCommand(command, sources=sources) is False
    assert sock.close.called
