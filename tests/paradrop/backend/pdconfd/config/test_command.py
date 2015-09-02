import tempfile

from mock import MagicMock, patch
from nose.tools import assert_raises


@patch("paradrop.backend.pdconfd.config.command.out")
@patch("subprocess.Popen")
def test_Command_execute(Popen, out):
    """
    Test the Command.execute method
    """
    from paradrop.backend.pdconfd.config.command import Command

    proc = MagicMock()
    proc.stdout = ["output"]
    proc.stderr = ["error"]
    Popen.return_value = proc

    command = Command(0, ["callme"])
    command.parent = MagicMock()

    command.execute()
    assert out.verbose.called_once_with("callme: output")
    assert out.verbose.called_once_with("callme: error")
    assert command.parent.executed.append.called

    Popen.side_effect = Exception("Boom!")
    command.execute()
    assert out.info.called


@patch("paradrop.backend.pdconfd.config.command.Command.execute")
def test_KillCommand(execute):
    """
    Test the KillCommand class
    """
    from paradrop.backend.pdconfd.config.command import KillCommand

    # Test with a numeric pid.
    command = KillCommand(0, 12345)
    assert command.getPid() == 12345

    expected = ["kill", "12345"]
    command.execute()
    assert execute.called_once_with(expected)

    execute.reset_mock()

    pidFile = tempfile.NamedTemporaryFile(delete=True)
    pidFile.write("54321")
    pidFile.flush()

    # Test with a pid file.
    command = KillCommand(0, pidFile.name)
    assert command.getPid() == 54321

    expected = ["kill", "54321"]
    command.execute()
    assert execute.called_once_with(expected)
    
    execute.reset_mock()

    # Test with a non-existent pid file.
    command = KillCommand(0, "")
    assert command.getPid() is None
    
    command.execute()
    assert not execute.called
