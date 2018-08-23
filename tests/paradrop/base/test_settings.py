import os

from mock import patch


def test_parse_value():
    """
    Test parseValue function
    """
    from paradrop.base.settings import parseValue

    assert parseValue("True") is True
    assert parseValue("true") is True
    assert parseValue("False") is False
    assert parseValue("false") is False
    assert parseValue("None") is None
    assert parseValue("none") is None

    result = parseValue("3.14")
    assert isinstance(result, float)
    assert result == float("3.14")

    result = parseValue("42")
    assert isinstance(result, int)
    assert result == 42

    result = parseValue("hello")
    assert isinstance(result, basestring)
    assert result == "hello"

    result = parseValue("out.txt")
    assert isinstance(result, basestring)
    assert result == "out.txt"


def test_load_settings():
    """
    Test updateSettings function
    """
    from paradrop.base import settings

    with patch.dict(os.environ, {'DEBUG_MODE': 'true'}):
        settings.loadSettings("unittest", ["PD_TEST_VAR:stuff"])

        assert settings.PD_TEST_VAR == "stuff"
        assert settings.DEBUG_MODE is True
