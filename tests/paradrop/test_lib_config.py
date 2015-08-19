from .mock import MockChute, MockUpdate


def test_get_network_config_wifi():
    """
    Test generating configuration for chute WiFi interface.
    """
    from paradrop.lib.config.network import getNetworkConfigWifi

    # Set up enough fake data to make call.
    update = object()
    cfg = dict()
    cfg['type'] = "wifi"
    cfg['ssid'] = "Paradrop"
    iface = dict()
    iface['device'] = "wlan0"

    getNetworkConfigWifi(update, "mywifi", cfg, iface)

    # Check that all of the keys made it into the output.
    keys = ["subnet", "ssid", "ipaddrWithPrefix", "externalIntf",
            "externalIpaddr", "netmask", "extIntfNumber", "internalIpaddr",
            "device", "extIntfPrefix"]
    assert all(k in iface for k in keys)


def test_get_network_config():
    """
    Test generating network configuration for a chute update.
    """
    from paradrop.lib.config.network import getNetworkConfig, abortNetworkConfig

    update = MockUpdate()
    update.old = None
    update.new = MockChute()
    update.new.net = {
        'mywifi': {
            'type': 'wifi',
            'intfName': 'wlan0',
            'ssid': 'Paradrop',
            'encryption': 'psk2',
            'key': 'password'
        }
    }
    update.new.setCache("networkInterfaces", {})

    devices = {
        'wifi': [{'name': 'wlan0'}]
    }
    update.new.setCache("networkDevices", devices)

    getNetworkConfig(update)
    abortNetworkConfig(update)
