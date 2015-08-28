import os

from mock import MagicMock, Mock, patch


def test_getArgs():
    """
    Test pdinstall.main.getArgs
    """
    from pdinstall.main import getArgs

    argv = ["install", "--source", "paradrop_0.1.0_all.snap"]
    args = getArgs(argv)
    assert args.sources == [argv[2]]


@patch("os.remove")
@patch("os.listdir")
def test_cleanupServiceFiles(listdir, remove):
    """
    Test pdinstall.main.cleanupServiceFiles
    """
    from pdinstall.main import SERVICE_FILES_DIR, cleanupServiceFiles

    listdir.return_value = ["paradrop_pd_0.1.0.service", "syslog.service"]
    cleanupServiceFiles("paradrop")

    path = os.path.join(SERVICE_FILES_DIR, "paradrop_pd_0.1.0.service")
    remove.assert_called_once_with(path)


@patch("pdinstall.snappy.Snap.getFile")
def test_getSnaps(getFile):
    """
    Test pdinstall.main.getSnaps
    """
    from pdinstall.main import getSnaps

    sources = ["paradrop_0.2.0_all.snap", "paradrop_0.1.0_all.snap"]
    getFile.return_value = True

    snaps = getSnaps(sources)
    assert len(snaps) == 2

    getFile.return_value = False

    snaps = getSnaps(sources)
    assert snaps == []


@patch("pdinstall.main.cleanupServiceFiles")
@patch("pdinstall.snappy.installSnap")
def test_installFromList(installSnap, cleanupServiceFiles):
    """
    Test pdinstall.main.installFromList
    """
    from pdinstall.main import installFromList

    args = Mock()
    args.ignore_version = False

    snaps = list()
    snaps.append(MagicMock())
    snaps[0].name = "paradrop"
    snaps[0].isInstalled.return_value = True

    assert installFromList(snaps, args)

    snaps[0].isInstalled.return_value = False
    installSnap.return_value = True

    assert installFromList(snaps, args)

    installSnap.return_value = False

    assert installFromList(snaps, args) is False
    assert cleanupServiceFiles.called_once_with("paradrop")


@patch("pdinstall.main.installFromList")
@patch("pdinstall.main.getSnaps")
@patch("pdinstall.main.getArgs")
def test_main(getArgs, getSnaps, installFromList):
    """
    Test pdinstall.main.main
    """
    from pdinstall.main import main

    installFromList.return_value = True

    args = Mock()
    args.command = "install"
    args.sources = ["fake.snap"]
    getArgs.return_value = args

    assert main() == 0
    assert getArgs.called
    assert getSnaps.called

    installFromList.return_value = False

    assert main() != 0
