from mock import MagicMock


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
