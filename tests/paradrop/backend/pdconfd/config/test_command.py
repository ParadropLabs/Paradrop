import tempfile

from mock import MagicMock, patch
from nose.tools import assert_raises


@patch("subprocess.Popen")
def test_Command_execute(Popen):
    """
    Test the Command.execute method
    """
    from paradrop.backend.pdconfd.config.command import Command

    command = Command(0, [])
    command.parent = MagicMock()

    command.execute()
    assert command.parent.executed.append.called


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
