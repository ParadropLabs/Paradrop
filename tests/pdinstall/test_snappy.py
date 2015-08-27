from mock import MagicMock, Mock, patch
from nose.tools import assert_raises


@patch("os.path.isfile")
def test_snap(isfile):
    """
    Test Snap class
    """
    from pdinstall.snappy import Snap

    # Should raise exception because file does not exist
    isfile.return_value=False
    assert_raises(Exception, Snap, "bad.snap")

    # Should raise exception because the name is invalid
    isfile.return_value=True
    assert_raises(Exception, Snap, "bad.snap")

    isfile.return_value=True
    snap = Snap("paradrop_0.1.0_all.snap")
    assert snap.name == "paradrop"
    assert snap.version == "0.1.0"
    assert snap.arch == "all"
    assert str(snap) == "paradrop_0.1.0"

    with patch("pdinstall.snappy.urllib.urlretrieve") as urlretrieve:
        snap.source = "http://example.org/paradrop_0.1.0_all.snap"
        isfile.return_value = True
        assert snap.getFile()
        assert urlretrieve.called

    with patch("pdinstall.snappy.isInstalled") as isInstalled:
        isInstalled.return_value = True
        assert snap.isInstalled()
        assert snap.isInstalled(ignoreVersion=True)


def test_callSnappy():
    """
    Test pdinstall.snappy.callSnappy
    """
    from pdinstall.snappy import callSnappy

    with patch("pdinstall.snappy.subprocess") as subprocess:
        proc = MagicMock()
        subprocess.Popen.return_value = proc
        proc.stdout = ["Output message"]
        proc.stderr = ["Error message"]
        proc.returncode = 0

        assert callSnappy("install")
        assert proc.wait.called

        subprocess.Popen.side_effect = Exception("Boom!")
        assert callSnappy("install") is False


@patch("pdinstall.snappy.callSnappy")
@patch("shutil.rmtree")
@patch("os.path.exists")
def test_installSnap(exists, rmtree, callSnappy):
    """
    Test pdinstall.snappy.installSnap
    """
    from pdinstall.snappy import installSnap

    snap = Mock()
    snap.isInstalled = Mock(side_effect=[False, True, True])
    exists.return_value = True
    callSnappy.return_value = True

    assert installSnap(snap)
    assert rmtree.called

    snap.isInstalled.side_effect = None
    snap.isInstalled.return_value = False
    callSnappy.return_value = False

    assert installSnap(snap) is False


def test_parseSnappyList():
    """
    Test pdinstall.snappy.parseSnappyList
    """
    from pdinstall.snappy import parseSnappyList

    source = [
        "Name Date Version Developer",
        "bad line",
        "paradrop 2015-01-01 0.1.0"
    ]
    snaps = parseSnappyList(source)
    assert snaps == {'paradrop': ['0.1.0']}


def test_installedSnaps():
    """
    Test pdinstall.snappy.installedSnaps
    """
    from pdinstall.snappy import installedSnaps

    with patch("pdinstall.snappy.subprocess") as subprocess:
        proc = MagicMock()
        subprocess.Popen.return_value = proc
        proc.stdout = [
            "Name Date Version Developer",
            "bad line",
            "paradrop 2015-01-01 0.1.0"
        ]

        snaps = installedSnaps()
        assert snaps == {'paradrop': ['0.1.0']}

        subprocess.Popen.side_effect = Exception("Boom!")
        assert_raises(Exception, installedSnaps)


def test_isInstalled():
    """
    Test pdinstall.snappy.isInstalled
    """
    from pdinstall.snappy import isInstalled

    with patch("pdinstall.snappy.installedSnaps") as installedSnaps:
        installedSnaps.return_value = {}
        assert isInstalled("paradrop") is False
        installedSnaps.return_value = {"paradrop": ["0.1.0"]}
        assert isInstalled("paradrop")
        assert isInstalled("paradrop", "0.1.0")
        assert isInstalled("paradrop", "0.2.0") is False
