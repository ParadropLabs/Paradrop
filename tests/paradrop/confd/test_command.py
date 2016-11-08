import tempfile

from mock import MagicMock, patch
from nose.tools import assert_raises


def test_CommandList():
    """
    Test the CommandList class
    """
    from paradrop.confd.command import CommandList

    clist = CommandList()
    clist.append(20, "b")
    clist.append(20, "c")
    clist.append(10, "a")

    commands = list(clist.commands())
    assert commands == ["a", "b", "c"]


@patch("paradrop.confd.command.out")
@patch("subprocess.Popen")
def test_Command_execute(Popen, out):
    """
    Test the Command.execute method
    """
    from paradrop.confd.command import Command

    proc = MagicMock()
    proc.stdout = ["output"]
    proc.stderr = ["error"]
    Popen.return_value = proc

    command = Command(["callme"])
    command.parent = MagicMock()

    command.execute()
    assert out.verbose.called_once_with("callme: output")
    assert out.verbose.called_once_with("callme: error")
    assert command.parent.executed.append.called

    Popen.side_effect = Exception("Boom!")
    command.execute()
    assert out.info.called


@patch("paradrop.confd.command.Command.execute")
def test_KillCommand(execute):
    """
    Test the KillCommand class
    """
    from paradrop.confd.command import KillCommand

    # Test with a numeric pid.
    command = KillCommand(12345)
    assert command.getPid() == 12345

    expected = ["kill", "12345"]
    command.execute()
    assert execute.called_once_with(expected)

    execute.reset_mock()

    pidFile = tempfile.NamedTemporaryFile(delete=True)
    pidFile.write("54321")
    pidFile.flush()

    # Test with a pid file.
    command = KillCommand(pidFile.name)
    assert command.getPid() == 54321

    expected = ["kill", "54321"]
    command.execute()
    assert execute.called_once_with(expected)
    
    execute.reset_mock()

    # Test with a non-existent pid file.
    command = KillCommand("")
    assert command.getPid() is None
    
    command.execute()
    assert not execute.called
