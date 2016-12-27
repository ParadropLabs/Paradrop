from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.lib.container.downloader import Downloader


def test_github_re():
    from paradrop.lib.container.downloader import github_re
    assert github_re.match("https://github.com/user/pro.jec-t") is not None
    assert github_re.match("https://github.com/user/pro.jec-t.git") is not None


def test_Downloader():
    downloader = Downloader("http://example.com")

    # Abstract base class does not implement these methods.
    assert_raises(NotImplementedError, downloader.download)
    assert_raises(NotImplementedError, downloader.meta)

    # Mock out those methods and check that fetch calls them.
    downloader.download = MagicMock()
    downloader.meta = MagicMock()
    downloader.fetch()
    assert downloader.download.called
    assert downloader.meta.called


@patch("paradrop.lib.container.downloader.tarfile")
def test_Downloader_extract(tarfile):
    downloader = Downloader("http://example.com")
    downloader.tarFile = "/tmp/test.tar"
    downloader.workDir = "/tmp"

    tar = MagicMock()
    tarfile.open.return_value = tar

    badfile = MagicMock()
    badfile.name = ".."
    tar.__iter__.return_value = [badfile]

    # Exception: Archive contains a forbidden path: ..
    assert_raises(Exception, downloader.extract)

    badfile.name = "/bin/bash"
    tar.__iter__.return_value = [badfile]

    # Exception: Archive contains an absolute path: /bin/bash
    assert_raises(Exception, downloader.extract)

    srcdir = MagicMock()
    srcdir.name = "project-0123456789abcdef"
    tar.__iter__.return_value = [srcdir]

    # Exception: Repository does not contain a Dockerfile
    assert_raises(Exception, downloader.extract)

    dockerfile = MagicMock()
    dockerfile.name = "project-0123456789abcdef/Dockerfile"
    tar.__iter__.return_value = [srcdir, dockerfile]

    rundir = downloader.extract()
    assert rundir == "/tmp/project-0123456789abcdef"
