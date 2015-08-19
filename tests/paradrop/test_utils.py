class MockChute:
    def __init__(self, name="mock"):
        self.name = name
        self.IPs = list()
        self.SSIDs = list()

    def getChuteIPs(self):
        return self.IPs

    def getChuteSSIDs(self):
        return self.SSIDs


class MockChuteStorage:
    def __init__(self):
        self.chuteList = list()

    def getChuteList(self):
        return self.chuteList


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
    storage = MockChuteStorage()
    storage.chuteList.append(chute)

    # TODO: Fix this one.
#    assert not addresses.isIpAvailable("192.168.1.1", storage, "second")
    assert addresses.isIpAvailable("192.168.2.1", storage, "second")
    assert addresses.isIpAvailable("192.168.1.1", storage, "first")
    
    assert not addresses.isWifiSSIDAvailable("Paradrop", storage, "second")
    assert addresses.isWifiSSIDAvailable("available", storage, "second")
    assert addresses.isWifiSSIDAvailable("Paradrop", storage, "first")
