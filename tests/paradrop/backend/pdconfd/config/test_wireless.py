from mock import MagicMock


def test_ConfigWifiIface_update():
    """
    Test the update method on ConfigWifiIface
    """
    from paradrop.backend.pdconfd.config.wireless import ConfigWifiIface

    allConfigs = MagicMock()

    config1 = ConfigWifiIface()
    config1.mode = "sta"

    config2 = ConfigWifiIface()
    config2.mode = "ap"

    # Changing mode not supported
    assert config1.update(config2, allConfigs) is None

    # sta mode is completely unsupported
    config2.mode = "sta"
    assert config1.update(config2, allConfigs) is None
