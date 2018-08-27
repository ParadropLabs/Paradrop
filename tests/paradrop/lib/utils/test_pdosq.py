import os
import tempfile

from paradrop.lib.utils import pdosq


def test_safe_remove():
    fd, path = tempfile.mkstemp()
    os.close(fd)

    # The first call should return True (file removed).
    assert pdosq.safe_remove(path) is True

    # The second call should return False (no file removed).
    assert pdosq.safe_remove(path) is False

