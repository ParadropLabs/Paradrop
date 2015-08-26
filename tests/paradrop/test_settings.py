import os

from mock import patch


def test_parse_value():
    """
    Test parseValue function
    """
    from paradrop.lib.settings import parseValue

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


def test_update_settings():
    """
    Test updateSettings function
    """
    from paradrop.lib import settings

    with patch.dict(os.environ, {'PDFCD_PORT': '-1'}):
        settings.updateSettings(["PD_TEST_VAR:stuff"])

        assert settings.PD_TEST_VAR == "stuff"
        assert settings.PDFCD_PORT == -1

    with patch.dict(os.environ, {'SNAP_APP_DATA_PATH': '/stuff'}):
        settings.updateSettings()

        assert settings.FC_CHUTESTORAGE_SAVE_PATH.startswith("/stuff")
        assert settings.UCI_CONFIG_DIR.startswith("/stuff")
