from mock import MagicMock


def test_ConfigWifiIface_apply():
    """
    Test the ConfigWifiIface apply method
    """
    from paradrop.backend.pdconfd.config.wireless import ConfigWifiIface

    wifiDevice = MagicMock()
    interface = MagicMock()

    allConfigs = {
        ("wifi-device", "wlan0"): wifiDevice,
        ("interface", "lan"): interface
    }

    config = ConfigWifiIface()
    config.manager = MagicMock()
    config.makeHostapdConf = MagicMock()

    config.device = "wlan0"
    config.mode = "ap"
    config.ssid = "Paradrop"
    config.network = "lan"
    config.encryption = "psk2"
    config.key = "password"

    # First case: we are configuring the main interface.
    wifiDevice.name = "wlan0"
    interface.config_ifname = "wlan0"

    commands = config.apply(allConfigs)
    expected = "iw dev wlan0 set type __ap"
    assert any(expected in cmd[1] for cmd in commands)

    # Second case: we were given a desired vif name.
    interface.config_ifname = "br-lan"
    config.ifname = "lan.wlan0"

    commands = config.apply(allConfigs)
    expected = "iw dev wlan0 interface add lan.wlan0 type __ap"
    assert any(expected in cmd[1] for cmd in commands)

    # Third case: we are basing the vif off its network name.
    interface.config_ifname = "v0000.wlan0"
    config.ifname = None

    commands = config.apply(allConfigs)
    expected = "iw dev wlan0 interface add v0000.wlan0 type __ap"
    assert any(expected in cmd[1] for cmd in commands)
