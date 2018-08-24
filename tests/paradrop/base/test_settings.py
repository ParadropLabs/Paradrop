import os
import tempfile

from mock import patch

from paradrop.base import settings


def test_iterate_module_attributes():
    count = 0
    for name, value in settings.iterate_module_attributes(settings):
        assert getattr(settings, name) == value
        count += 1

    assert count > 0


def test_parse_value():
    """
    Test parseValue function
    """
    assert settings.parseValue("True") is True
    assert settings.parseValue("true") is True
    assert settings.parseValue("False") is False
    assert settings.parseValue("false") is False
    assert settings.parseValue("None") is None
    assert settings.parseValue("none") is None

    result = settings.parseValue("3.14")
    assert isinstance(result, float)
    assert result == float("3.14")

    result = settings.parseValue("42")
    assert isinstance(result, int)
    assert result == 42

    result = settings.parseValue("hello")
    assert isinstance(result, basestring)
    assert result == "hello"

    result = settings.parseValue("out.txt")
    assert isinstance(result, basestring)
    assert result == "out.txt"


def test_load_settings():
    """
    Test updateSettings function
    """
    with patch.dict(os.environ, {'DEBUG_MODE': 'true'}):
        settings.loadSettings("unittest", ["PD_TEST_VAR:stuff"])

        assert settings.PD_TEST_VAR == "stuff"
        assert settings.DEBUG_MODE is True


TEST_CONFIG = """
[base]
portal_server_port = 4444
"""


def test_load_from_file():
    with tempfile.NamedTemporaryFile() as output:
        output.write(TEST_CONFIG)
        output.flush()

        print(output.name)
        with open(output.name, 'r') as source:
            print(source.read())

        settings.load_from_file(output.name)
        print(type(settings.PORTAL_SERVER_PORT))
        print(settings.PORTAL_SERVER_PORT == 4444)
        assert settings.PORTAL_SERVER_PORT == 4444
