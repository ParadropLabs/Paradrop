from mock import MagicMock


from paradrop.confd import network, qos


def test_qos():
    net_iface = network.ConfigInterface()
    net_iface.name = "wan"
    net_iface.ifname = ["eth0"]

    qos_iface = qos.ConfigInterface()
    qos_iface.name = "wan"
    qos_iface.enabled = True
    qos_iface.classgroup = "Group"
    qos_iface.upload = 1000

    group = qos.ConfigClassgroup()
    group.name = "Group"
    group.classes = "Default Special"
    group.default = "Default"

    class1 = qos.ConfigClass()
    class1.name = "Default"
    class1.avgrate = 50
    class1.priority = 1

    class2 = qos.ConfigClass()
    class2.name = "Special"
    class2.avgrate = 50
    class2.priority = 10

    classify1 = qos.ConfigClassify()
    classify1.name = "other-1"
    classify1.target = "Default"
    classify1.srchost = "192.168.128.5"
    classify1.proto = "udp"
    classify1.dstports = 53

    classify2 = qos.ConfigClassify()
    classify2.name = "other-2"
    classify2.target = "Special"
    classify2.dsthost = "192.168.1.1"
    classify2.proto = "tcp"
    classify2.srcports = 80

    classify3 = qos.ConfigClassify()
    classify3.name = "other-3"
    classify3.target = "Default"
    classify3.proto = "tcp"
    classify3.dstports = 80

    allConfigs = {
        ("network", "interface", "wan"): net_iface,
        ("qos", "interface", "wan"): qos_iface,
        ("qos", "classgroup", "Group"): group,
        ("qos", "class", "Default"): class1,
        ("qos", "class", "Special"): class2,
        ("qos", "classify", "other-1"): classify1,
        ("qos", "classify", "other-2"): classify2,
        ("qos", "classify", "other-3"): classify3
    }

    net_iface.setup()
    group.setup()

    commands = qos_iface.apply(allConfigs)
    for cmd in commands:
        print(cmd[1])
    assert len(commands) > 0
