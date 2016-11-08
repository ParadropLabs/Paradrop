from mock import MagicMock


def test_ConfigRedirect_commands_dnat():
    """
    Test DNAT command generation
    """
    from paradrop.confd.firewall import ConfigRedirect

    eth0 = MagicMock()
    eth0.config_ifname = "eth0"

    wanZone = MagicMock()
    wanZone.interfaces.return_value = [eth0]

    allConfigs = {
        ("zone", "wan"): wanZone
    }

    config = ConfigRedirect()
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
