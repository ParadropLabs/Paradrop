import copy
import errno
import os
import tempfile

from mock import MagicMock, Mock, patch
from nose.tools import assert_raises

from .pdmock import MockChute, MockChuteStorage, writeTempFile

from paradrop.lib.utils import pdos
from paradrop.lib.utils import pdosq
from paradrop.lib.utils.storage import PDStorage


NETWORK_WAN_CONFIG = """
config interface wan #__PARADROP__
    option ifname 'eth0'
    option proto 'dhcp'
"""


class TestStorage(PDStorage):
    def __init__(self, filename):
        super(TestStorage, self).__init__(filename, None, None)
        self.data = None

    def setAttr(self, data):
        self.data = data

    def getAttr(self):
        return self.data

    def attrSaveable(self):
        return (self.data is not None)


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

def test_pdos():
    """
    Test pdos utility module
    """
    assert pdos.getMountCmd() == "mount"
    assert pdos.isMount("/")
    assert pdos.ismount("/")

    assert pdos.oscall("true") is None
    assert pdos.oscall("false") is not None
    assert pdos.oscall("echo hello") is None
    assert pdos.oscall("echo hello 1>&2") is None

    assert pdos.syncFS() is None

    # Make a file, check that our functions respond correctly to it
    path = writeTempFile("hello")
    assert pdos.fixpath(path) == path
    assert "text" in pdos.getFileType(path)
    assert pdos.exists(path)
    assert not pdos.isdir(path)
    assert pdos.isfile(path)

    # Remove the file, check that our functions detect that
    pdos.unlink(path)
    assert pdos.fixpath(path) == path
    assert pdos.getFileType(path) is None
    assert not pdos.exists(path)
    assert not pdos.isdir(path)
    assert not pdos.isfile(path)

    # Make a directory there instead
    pdos.mkdir(path)
    assert pdos.fixpath(path) == path
    assert "directory" in pdos.getFileType(path)
    assert pdos.exists(path)
    assert pdos.isdir(path)
    assert not pdos.isfile(path)

    # Now we will do some manipulations on files under that directory
    a = os.path.join(path, "a")
    b = os.path.join(path, "b")
    c = os.path.join(path, "c")
    d = os.path.join(path, "d")

    pdos.write(a, "hello")
    assert pdos.isfile(a)
    pdos.copy(a, b)
    assert pdos.isfile(b)
    pdos.symlink(a, c)
    assert pdos.isfile(c)
    pdos.move(a, b)
    assert not pdos.isfile(a)
    pdos.remove(b)
    assert not pdos.isfile(b)
    pdos.mkdir(a)
    pdos.copytree(a, b)
    assert pdos.isdir(b)

    # Remove a non-empty directory
    pdos.remove(path)
    assert not pdos.isdir(path)

    # This file is under a directory that no longer exists, so the write must
    # fail.
    #
    # TODO: These should not fail silently.  They should either return an error
    # indicator or raise an exception.
    pdos.writeFile(a, "c")
    pdos.write(a, "c")

    # Test various ways to call writeFile
    pdos.writeFile(path, ["a", "b"])
    pdos.writeFile(path, "c")
    pdos.writeFile(path, 5)  # This one does nothing.

    # Test the content with readFile
    data = pdos.readFile(path, array=False, delimiter="")
    assert data == "abc"
    data = pdos.readFile(path, array=True)
    assert data == ["a", "b", "c"]
    pdos.remove(path)
    assert pdos.readFile(path) is None


def test_pdosq():
    """
    Test pdosq utility functions
    """
    # Test makedirs with an already-exists error, returns False.
    with patch('os.makedirs', side_effect=OSError(errno.EEXIST, "error")):
        assert pdosq.makedirs("/") is False

    # Test makedirs with a permission error, passes on the Exception.
    with patch('os.makedirs', side_effect=OSError(errno.EPERM, "error")):
        assert_raises(OSError, pdosq.makedirs, "/")


def test_storage():
    """
    Test PDStorage class
    """
    temp = tempfile.mkdtemp()
    filename = os.path.join(temp, "storage")

    storage = PDStorage(filename, MagicMock(), None)

    # Constructor should have called this start function.
    assert storage.repeater.start.called

    # PDStorage needs to be subclassed; the base class always returns not
    # saveable.
    assert storage.attrSaveable() is False
    
    storage = TestStorage(filename)
    data = {"key": "value"}

    with open(filename, "w") as output:
        output.write("BAD CONTENTS")

    # The first attempt to read it will fail and try to delete the file.  We
    # will cause the unlink to fail on the first try and let it succeed on the
    # second try.
    with patch("paradrop.lib.utils.pdos.unlink", side_effect=Exception("Boom!")): 
        storage.loadFromDisk()
        assert os.path.exists(filename)
    storage.loadFromDisk()
    assert not os.path.exists(filename)

    # The first write will fail because we have not provided data yet.
    storage.saveToDisk()
    assert not os.path.exists(filename)

    # Now we will save some data and verify that we can reload it.
    storage.setAttr(data)

    # Cause the save to fail on the first try, then let it succeed.
    with patch("paradrop.lib.utils.pdos.open", side_effect=Exception("Boom!")):
        storage.saveToDisk()
        assert not os.path.exists(filename)
    storage.saveToDisk()
    assert os.path.exists(filename)

    storage.setAttr(None)
    storage.loadFromDisk()
    assert storage.getAttr() == data

    # Clean up
    pdos.remove(temp)


def test_uci():
    """
    Test UCI file utility module
    """
    from paradrop.lib.utils import uci
    from paradrop.lib import settings

    # Test functions for finding path to UCI files
    settings.UCI_CONFIG_DIR = "/tmp/config.d"
    assert uci.getSystemConfigDir() == "/tmp/config.d"
    assert uci.getSystemPath("network") == "/tmp/config.d/network"

    # Test stringify function
    assert uci.stringify("a") == "a"
    blob = {"a": "b"}
    assert uci.stringify(blob) == blob
    blob = {"a": {"b": "c"}}
    assert uci.stringify(blob) == blob
    blob = {"a": ["b", "c"]}
    assert uci.stringify(blob) == blob
    blob = {"a": 5}
    strblob = {"a": "5"}
    assert uci.stringify(blob) == strblob
    assert uci.isMatch(blob, strblob)

    # Write a realistic configuration and load with uci module
    path = writeTempFile(NETWORK_WAN_CONFIG)
    config = uci.UCIConfig(path)

    # Test if it found the config section that we know should be there
    empty = {}
    assert config.getConfig(empty) == []
    match = {"type": "interface", "name": "wan", "comment": "__PARADROP__"}
    assert len(config.getConfig(match)) == 1
    match = {"type": "interface", "name": "wan", "comment": "chute"}
    assert config.getConfig(match) == []
    assert config.getConfigIgnoreComments(empty) == []
    assert len(config.getConfigIgnoreComments(match)) == 1

    # More existence tests
    assert not config.existsConfig(empty, empty)
    match_config = {
        "type": "interface",
        "name": "wan",
        "comment": "__PARADROP__"
    }
    match_options = {
        "ifname": "eth0",
        "proto": "dhcp"
    }
    assert config.existsConfig(match_config, match_options)

    # Test adding and removing
    config.delConfigs([(match_config, match_options)])
    assert not config.existsConfig(match_config, match_options)
    config.addConfigs([(match_config, match_options)])
    assert config.existsConfig(match_config, match_options)
    config.delConfig(match_config, match_options)
    assert not config.existsConfig(match_config, match_options)
    config.addConfig(match_config, match_options)
    assert config.existsConfig(match_config, match_options)

    # Get configuration by chute name
    assert config.getChuteConfigs("none") == []
    assert len(config.getChuteConfigs("__PARADROP__")) == 1

    # Test saving and reloading
    config.save(backupToken="backup")
    config2 = uci.UCIConfig(path)

    # Simple test for the equality operators
    assert config == config2
    assert not (config != config2)

    # Test chuteConfigsMatch function
    assert not uci.chuteConfigsMatch(config.getChuteConfigs("__PARADROP__"),
            config2.getChuteConfigs("none"))
    assert uci.chuteConfigsMatch(config.getChuteConfigs("__PARADROP__"),
            config2.getChuteConfigs("__PARADROP__"))

    # Further test the equality operators
    config2.filepath = "NOMATCH"
    assert not (config == config2)
    assert config != config2

    config2.filepath = config.filepath
    config2.myname = "NOMATCH"
    assert not (config == config2)
    assert config != config2

    config2.myname = config.myname
    config2.config = []
    assert not (config == config2)
    assert config != config2


def test_uci_getLineParts():
    """
    Test the UCI getLineParts utility function
    """
    from paradrop.lib.utils import uci

    line = "config interface wan"
    result = uci.getLineParts(line)
    assert result == line.split()

    # It should eat the apostrophes and give same result.
    line2 = "config 'interface' 'wan'"
    result2 = uci.getLineParts(line)
    assert result2 == result

    line = "option key 'my password has spaces'"
    result = uci.getLineParts(line)
    assert result == ["option", "key", "my password has spaces"]

    line = "config interface 'oops"
    result = uci.getLineParts(line)
    assert result == ["config", "interface", "oops"]
