import os
import tempfile

from paradrop.lib.utils import pdosq


def test_read_yaml_file():
    fd, path = tempfile.mkstemp()
    os.close(fd)

    with open(path, "w") as output:
        output.write("value: 42\n")

    result = pdosq.read_yaml_file(path)
    assert result['value'] == 42

    pdosq.safe_remove(path)
    assert pdosq.read_yaml_file(path, default=None) is None
    assert pdosq.read_yaml_file(path, default={}) == {}


def test_safe_remove():
    fd, path = tempfile.mkstemp()
    os.close(fd)

    # The first call should return True (file removed).
    assert pdosq.safe_remove(path) is True

    # The second call should return False (no file removed).
    assert pdosq.safe_remove(path) is False

