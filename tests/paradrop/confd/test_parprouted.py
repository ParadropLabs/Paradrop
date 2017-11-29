from mock import MagicMock


from paradrop.confd import manager, network, parprouted


def test_definitions():
    assert "parprouted:bridge" in manager.configTypeMap


def test_bridge():
    interface1 = network.ConfigInterface()
    interface1.name = "wan"
    interface1.config_ifname = "eth0"

    interface2 = network.ConfigInterface()
    interface2.name = "vwlan0"
    interface2.config_ifname = "vwlan0"

    allConfigs = {
        ("network", "interface", "wan"): interface1,
        ("network", "interface", "vwlan0"): interface2
    }

    bridge = parprouted.ConfigBridge()
    bridge.interfaces = ["wan", "vwlan0"]

    commands = bridge.apply(allConfigs)
    assert len(commands) > 0
