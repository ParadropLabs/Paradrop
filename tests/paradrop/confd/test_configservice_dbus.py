from mock import MagicMock


def test_ConfigServiceDbus():
    """
    Test the ConfigService class
    """
    from paradrop.confd.configservice_dbus import ConfigServiceDbus

    manager = MagicMock()

    service = ConfigServiceDbus(manager)

    service.dbus_Reload("test")
    assert manager.loadConfig.called_once_with("test")

    service.dbus_ReloadAll()
    assert manager.loadConfig.called_once_with()

    assert service.dbus_Test()

    service.dbus_UnloadAll()
    assert manager.unload.called_once_with()

    service.dbus_WaitSystemUp()
    assert manager.waitSystemUp.called_once_with()
