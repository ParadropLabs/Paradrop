from mock import MagicMock


def test_interpretBoolean():
    from paradrop.confd.base import interpretBoolean

    assert interpretBoolean("0") is False
    assert interpretBoolean("1") is True

    assert interpretBoolean("False") is False
    assert interpretBoolean("True") is True


def test_ConfigObject():
    """
    Test the ConfigObject class
    """
    from paradrop.confd.base import ConfigObject

    config = ConfigObject()
    config.typename = "type"
    assert str(config) == "config type"

    config = ConfigObject()
    config.typename = "type"
    config.name = "name"
    assert str(config) == "config type name"
