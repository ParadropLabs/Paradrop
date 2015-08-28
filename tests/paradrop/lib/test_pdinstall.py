from mock import MagicMock, patch


@patch("socket.socket")
def test_sendCommand(socket):
    """
    Test paradrop.lib.pdinstall.sendCommand
    """
    from paradrop.lib.pdinstall import sendCommand

    command = "install"
    data = {
        'sources': ["paradrop_0.1.0_all.snap"]
    }

    sock = MagicMock()
    socket.return_value = sock

    assert sendCommand(command, data)
    assert sock.connect.called
    assert sock.send.called
    assert sock.close.called

    sock.reset_mock
    sock.connect.side_effect = Exception("Boom!")

    assert sendCommand(command, data) is False
    assert sock.close.called
