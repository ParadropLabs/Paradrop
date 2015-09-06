from mock import MagicMock


def test_ConfigWifiIface_apply():
    """
    Test the apply method on ConfigWifiIface
    """
    from paradrop.backend.pdconfd.config.wireless import ConfigWifiIface

    wifiDevice = MagicMock()
    wifiDevice.name = "wlan0"

    interface = MagicMock()
    interface.config_ifname = "wlan0"

    allConfigs = {
        ("wifi-device", "wlan0"): wifiDevice,
        ("interface", "wifi"): interface
    }

    # This config tests the specific case in which 
    # wifiDevice.name == interface.config_ifname
    config = ConfigWifiIface()
    config.manager = MagicMock()
    config.device = "wlan0"
    config.mode = "ap"
    config.network = "wifi"

    # Override this function that wants to write a file.
    config.makeHostapdConf = MagicMock()

    commands = config.apply(allConfigs)
    for cmd in commands:
        print(cmd)
    assert len(commands) == 1
