from mock import MagicMock


def test_ConfigServicRpc():
    """
    Test the ConfigService class
    """
    from paradrop.confd.configservice_rpc import ConfigServiceRpc

    manager = MagicMock()

    service = ConfigServiceRpc(manager)

    service.remote_Reload("test")
    assert manager.loadConfig.called_once_with("test")

    service.remote_ReloadAll()
    assert manager.loadConfig.called_once_with()

    assert service.remote_Test()

    service.remote_UnloadAll()
    assert manager.unload.called_once_with()

    service.remote_WaitSystemUp()
    assert manager.waitSystemUp.called_once_with()
