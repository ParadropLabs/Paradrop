from .mock import MockChute, MockChuteStorage


def test_addresses():
    """
    Test IP address utility functions
    """
    from paradrop.lib.utils import addresses

    ipaddr = "192.168.1.1"
    assert addresses.isIpValid(ipaddr)

    ipaddr = "192.168.1.256"
    assert not addresses.isIpValid(ipaddr)

    chute = MockChute(name="first")
    chute.IPs.append("192.168.1.1")
    chute.SSIDs.append("Paradrop")
    chute.staticIPs.append("192.168.33.1")
    storage = MockChuteStorage()
    storage.chuteList.append(chute)

    assert not addresses.isIpAvailable("192.168.1.1", storage, "second")
    assert addresses.isIpAvailable("192.168.2.1", storage, "second")
    assert addresses.isIpAvailable("192.168.1.1", storage, "first")
    
    assert not addresses.isWifiSSIDAvailable("Paradrop", storage, "second")
    assert addresses.isWifiSSIDAvailable("available", storage, "second")
    assert addresses.isWifiSSIDAvailable("Paradrop", storage, "first")

    assert not addresses.isStaticIpAvailable("192.168.33.1", storage, "second")
    assert addresses.isStaticIpAvailable("192.168.35.1", storage, "second")
    assert addresses.isStaticIpAvailable("192.168.33.1", storage, "first")

    assert not addresses.checkPhyExists(-100)

    ipaddr = "192.168.1.1"
    netmask = "255.255.255.0"

    assert addresses.incIpaddr("192.168.1.1") == "192.168.1.2"
    assert addresses.incIpaddr("fail") is None

    assert addresses.maxIpaddr(ipaddr, netmask) == "192.168.1.254"
    assert addresses.maxIpaddr(ipaddr, "fail") is None

    assert addresses.getSubnet(ipaddr, netmask) == "192.168.1.0"
    assert addresses.getSubnet(ipaddr, "fail") is None

    # Test with nothing in the cache
    assert addresses.getInternalIntfList(chute) is None
    assert addresses.getGatewayIntf(chute) == (None, None)
    assert addresses.getWANIntf(chute) is None

    # Now put an interface in the cache
    ifaces = [{
        'internalIntf': "eth0",
        'netType': "wan",
        'externalIpaddr': "192.168.1.1"
    }]
    chute.setCache("networkInterfaces", ifaces)

    assert addresses.getInternalIntfList(chute) == ["eth0"]
    assert addresses.getGatewayIntf(chute) == ("192.168.1.1", "eth0")
    assert addresses.getWANIntf(chute) == ifaces[0]
