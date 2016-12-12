from mock import MagicMock

from paradrop.confd import firewall


def test_ConfigRedirect_commands_dnat():
    """
    Test DNAT command generation
    """
    eth0 = MagicMock()
    eth0.config_ifname = "eth0"

    wanZone = MagicMock()
    wanZone.interfaces.return_value = [eth0]

    allConfigs = {
        ("firewall", "zone", "wan"): wanZone
    }

    config = firewall.ConfigRedirect()
    config.manager = MagicMock()
    config.target = "DNAT"
    config.proto = "tcp"
    config.src = "wan"

    config.src_ip = "1.2.3.4"
    config.src_dip = "192.168.1.1"
    config.src_port = 80
    config.src_dport = 8000
    config.dest_ip = "192.168.2.1"

    commands = config.apply(allConfigs)
    for cmd in commands:
        print(cmd[1])
    assert len(commands) == 1

    cmd = commands[0][1]
    assert "--source 1.2.3.4" in cmd
    assert "--destination 192.168.1.1" in cmd
    assert "--sport 80" in cmd
    assert "--dport 8000" in cmd
    assert "--jump DNAT --to-destination 192.168.2.1" in cmd

    config.dest_port = 9000

    commands = config.apply(allConfigs)
    for cmd in commands:
        print(cmd[1])
    assert len(commands) == 1

    cmd = commands[0][1]
    assert "--source 1.2.3.4" in cmd
    assert "--destination 192.168.1.1" in cmd
    assert "--sport 80" in cmd
    assert "--dport 8000" in cmd
    assert "--jump DNAT --to-destination 192.168.2.1:9000" in cmd

    config.dest_ip = None

    commands = config.apply(allConfigs)
    for cmd in commands:
        print(cmd[1])
    assert len(commands) == 1

    cmd = commands[0][1]
    assert "--source 1.2.3.4" in cmd
    assert "--destination 192.168.1.1" in cmd
    assert "--sport 80" in cmd
    assert "--dport 8000" in cmd
    assert "--jump REDIRECT --to-port 9000" in cmd

def test_ConfigRules():
    eth0 = MagicMock()
    eth0.config_ifname = "eth0"

    eth1 = MagicMock()
    eth1.config_ifname = "eth1"

    wanZone = MagicMock()
    wanZone.interfaces.return_value = [eth0]

    lanZone = MagicMock()
    lanZone.interfaces.return_value = [eth1]

    allConfigs = {
        ("firewall", "zone", "wan"): wanZone,
        ("firewall", "zone", "lan"): lanZone
    }

    config = firewall.ConfigRule()
    config.src = "wan"
    config.src_ip = "1.1.1.0/24"
    config.proto = "tcp"
    config.dest_ip = "192.168.1.1"
    config.dest_port = "80"
    config.target = "ACCEPT"

    commands = config.apply(allConfigs)
    assert len(commands) == 1

    commands = config.revert(allConfigs)
    assert len(commands) == 1

    config = firewall.ConfigRule()
    config.src = "wan"
    config.dest = "lan"
    config.src_ip = "1.1.1.0/24"
    config.proto = "tcp"
    config.dest_ip = "192.168.1.1"
    config.dest_port = "80"
    config.target = "ACCEPT"

    commands = config.apply(allConfigs)
    assert len(commands) == 1

    commands = config.revert(allConfigs)
    assert len(commands) == 1

    config = firewall.ConfigRule()
    config.dest = "wan"
    config.src_port = 53
    config.proto = "udp"
    config.dest_ip = "255.255.255.255"
    config.target = "ACCEPT"

    commands = config.apply(allConfigs)
    assert len(commands) == 1

    commands = config.revert(allConfigs)
    assert len(commands) == 1
