from mock import MagicMock


def test_ConfigService():
    """
    Test the ConfigService class
    """
    from paradrop.backend.pdconfd.main import ConfigService

    manager = MagicMock()

    ConfigService.configManager = manager
    service = ConfigService()

    service.dbus_Reload("test")
    assert manager.loadConfig.called_once_with("test")

    service.dbus_ReloadAll()
    assert manager.loadConfig.called_once_with()

    assert service.dbus_Test()

    service.dbus_UnloadAll()
    assert manager.unload.called_once_with()

    service.dbus_WaitSystemUp()
    assert manager.waitSystemUp.called_once_with()
