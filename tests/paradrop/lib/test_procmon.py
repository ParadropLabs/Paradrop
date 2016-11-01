from mock import patch, MagicMock

from paradrop.lib.procmon import ProcessMonitor


@patch("paradrop.lib.procmon.open")
@patch("paradrop.lib.procmon.os")
@patch("paradrop.lib.procmon.glob")
@patch("paradrop.lib.procmon.psutil")
def test_ProcessMonitor(psutil, glob, os, mock_open):
    mon = ProcessMonitor("foo")

    # No process or pid file.
    psutil.process_iter.return_value = []
    glob.iglob.return_value = []
    assert mon.check() is False

    proc = MagicMock()
    proc.pid = 1
    proc.name.return_value = "foo"

    # Found process but no pid file.
    psutil.process_iter.return_value = [proc]
    assert mon.check() is False

    pidfile = MagicMock(spec=file)
    pidfile.read.return_value = "2"
    mock_open.return_value = pidfile
    glob.iglob.return_value = ["ignored"]

    # Found process and stale pid file.  It should try to remove the pid file.
    assert mon.check() is False
    assert os.remove.called


@patch("paradrop.lib.procmon.subprocess")
def test_ProcessMonitor_restart(subprocess):
    mon = ProcessMonitor("test", action="reboot")
    mon.restart()
    assert subprocess.call.called
