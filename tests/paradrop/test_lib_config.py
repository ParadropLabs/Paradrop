import json
import os
import tempfile

from nose.tools import assert_raises
from mock import MagicMock, Mock, patch

from .pdmock import MockChute, MockUpdate

from paradrop.lib import settings
from paradrop.lib.utils import pdos


def fake_interface_list():
    interfaces = list()
    interfaces.append({
        'name': 'mywan',
        'netType': 'wan',
        'externalIntf': 'v0000.eth0',
        'externalIpaddr': '192.168.1.1'
    })
    interfaces.append({
        'name': 'mylan',
        'netType': 'lan',
        'externalIntf': 'v0000.eth1',
        'externalIpaddr': '192.168.2.1'
    })
    interfaces.append({
        'name': 'mywifi',
        'netType': 'wifi',
        'device': 'wlan0',
        'externalIntf': 'v0000.wlan0',
        'ssid': 'Paradrop',
        'encryption': 'psk2',
        'key': 'password',
        'externalIpaddr': '192.168.3.1',
        'internalIpaddr': '192.168.3.2',
        'dhcp': {
            'start': 100,
            'limit': 100,
            'lease': '12h',
            'dns': ['8.8.8.8']
        }
    })
    return interfaces


def mockExists(path):
    """
    Generate fake results for os.path.exists function
    """
    if path == "/sys/class/net/wlan0/wireless":
        return True
    return False


def mockListDir(path):
    """
    Generate fake results for os.listdir
    """
    if path == "/sys/class/net":
        return ["lo", "eth0", "eth1", "wlan0", "vethabcdef", "br-lan", "docker0"]
    else:
        return os.listdir(path)

def mockReadFile(filename):
    """
    Generate fake output for files
    """
    if filename == "/proc/net/route":
        routes = list()
        routes.append("Iface   Destination Gateway     Flags   RefCnt  Use Metric  Mask        MTU WindowIRTT")
        routes.append("eth0    00000000    DEADBEEF    0003    0   0   0   00000000    0   0   0")
        routes.append("eth0    DEADBEEF    00000000    0001    0   0   1   00FFFFFF    0   0   0")
        return routes
    else:
        return list()


def mockStatusString():
    """
    Generate a fake status string for pdconf reload
    """
    status = list()
    status.append({
        'comment': 'GoodChute',
        'success': True,
        'type': 'interface',
        'name': 'lan'
    })
    status.append({
        'comment': 'BadChute',
        'success': False,
        'type': 'interface',
        'name': 'lan'
    })
    return json.dumps(status)


def fake_rules_list():
    rules = list()
    rules.append({
        'name': 'rule1',
        'type': 'redirect',
        'from': '@host.lan:9000',
        'to': 'mywan:80'
    })
    return rules


@patch("paradrop.backend.pdconfd.client.reloadAll", mockStatusString)
def test_configservice():
    """
    Test paradrop.lib.config.configservice
    """
    from paradrop.lib.config import configservice

    # This one should succeed
    update = MockUpdate(name="GoodChute")
    assert configservice.reloadAll(update) is None

    # This one should raise an exception
    update = MockUpdate(name="BadChute")
    assert_raises(Exception, configservice.reloadAll, update)


@patch("paradrop.lib.utils.pdos.readFile", new=mockReadFile)
@patch("paradrop.lib.utils.pdos.exists", new=mockExists)
@patch("paradrop.lib.utils.pdos.listdir", new=mockListDir)
def test_config_devices():
    """
    Test paradrop.lib.config.devices
    """
    from paradrop.lib.config import devices

    # Test the isVirtual function
    assert devices.isVirtual("eth0") is False
    assert devices.isVirtual("v0000.eth0")
    assert devices.isVirtual("vethabcdef")

    assert devices.isWAN("eth0")
    assert devices.isWAN("wlan0") is False

    update = MockUpdate()
    update.old = None
    update.new = MockChute()

    hostConfig = {
        'wan': {
            'interface': 'eth0'
        },
        'lan': {
            'interfaces': ['eth1'],
            'ipaddr': '192.168.1.1',
            'netmask': '255.255.255.0',
            'dhcp': {
                'start': 100,
                'limit': 100,
                'leasetime': '12h'
            }
        },
        'wifi': [{'interface': 'wlan0', 'channel': 1}]
    }
    update.new.setCache('hostConfig', hostConfig)

    settings.UCI_CONFIG_DIR = tempfile.mkdtemp()

    # Calling before getSystemDevices should do nothing.
    devices.setSystemDevices(update)

    # Test normal flow---our mock functions will simulate the existence of
    # various network interfaces.
    devices.getSystemDevices(update)
    devices.setSystemDevices(update)

    cachedDevices = update.new.getCache("networkDevices")
    assert len(cachedDevices) == 3

    # Make sure it continues to work with missing devices.
    cachedDevices['lan'] = []
    devices.setSystemDevices(update)
    cachedDevices['wifi'] = []
    devices.setSystemDevices(update)
    cachedDevices['wan'] = []
    devices.setSystemDevices(update)

    pdos.remove(settings.UCI_CONFIG_DIR)


def test_config_dhcp():
    """
    Test paradrop.lib.config.dhcp
    """
    from paradrop.lib.config import dhcp

    update = MockUpdate()
    update.old = None
    update.new = MockChute()

    # Should do nothing before we set "networkInterfaces".
    dhcp.getVirtDHCPSettings(update)

    interfaces = fake_interface_list()
    update.new.setCache("networkInterfaces", interfaces)

    settings.UCI_CONFIG_DIR = tempfile.mkdtemp()

    # Test code path with caching enabled
    dhcp.DNSMASQ_CACHE_ENABLED = True
    dhcp.getVirtDHCPSettings(update)
    dhcp.setVirtDHCPSettings(update)

    # Test code path with caching disabled
    dhcp.DNSMASQ_CACHE_ENABLED = False
    dhcp.getVirtDHCPSettings(update)
    dhcp.setVirtDHCPSettings(update)

    pdos.remove(settings.UCI_CONFIG_DIR)

    # Test with missing "lease" field.
    interfaces.append({
        'name': 'broken',
        'dhcp': {
            'start': 100,
            'limit': 100
        }
    })
    assert_raises(Exception, dhcp.getVirtDHCPSettings, update)


def test_config_dockerconfig():
    """
    Test the dockerconfig module.
    """
    from paradrop.lib.config import dockerconfig

    update = Mock(updateType="create")

    # Test with missing attribute 'dockerfile'.
    del update.dockerfile
    dockerconfig.getVirtPreamble(update)
    assert not hasattr(update, "dockerfile")

    # Test with 'dockerfile' set to None.
    update.dockerfile = None
    dockerconfig.getVirtPreamble(update)
    assert update.dockerfile is None

    # Test with 'dockerfile' having contents.
    update.dockerfile = "docker"
    dockerconfig.getVirtPreamble(update)
    assert update.dockerfile.read() == "docker"


def test_config_firewall():
    """
    Test paradrop.lib.config.firewall
    """
    from paradrop.lib.config import firewall

    # Test findMatchingInterface function
    interfaces = fake_interface_list()
    assert firewall.findMatchingInterface("*wifi", interfaces) is not None
    assert firewall.findMatchingInterface("??lan", interfaces) is not None
    assert firewall.findMatchingInterface("missing", interfaces) is None

    update = MockUpdate()
    update.old = None
    update.new = MockChute()

    # No interfaces in the cache---should return without a problem
    firewall.getOSFirewallRules(update)
    firewall.getDeveloperFirewallRules(update)

    update.new.setCache("networkInterfaces", interfaces)
    firewall.getOSFirewallRules(update)
    result = update.new.getCache("osFirewallRules")
    assert len(result) == 4

    update.new.firewall = fake_rules_list()
    firewall.getDeveloperFirewallRules(update)
    result = update.new.getCache('developerFirewallRules')
    assert len(result) == 1

    # Need to make a writable location for our config files.
    settings.UCI_CONFIG_DIR = tempfile.mkdtemp()
    firewall.setOSFirewallRules(update)
    pdos.remove(settings.UCI_CONFIG_DIR)
 
    # Try a bad rule that has both from/to outside the chute.
    update.new.firewall = fake_rules_list()
    update.new.firewall.append({
        'name': 'bad',
        'type': 'redirect',
        'from': '@host.lan',
        'to': '@host.lan'
    })
    assert_raises(Exception, firewall.getDeveloperFirewallRules, update)

    # Try a bad rule that does not match an interface.
    update.new.firewall = fake_rules_list()
    update.new.firewall.append({
        'name': 'bad',
        'type': 'redirect',
        'from': '@host.lan',
        'to': 'missing'
    })
    assert_raises(Exception, firewall.getDeveloperFirewallRules, update)

    # Try an SNAT rule, which is not currently supported.
    update.new.firewall = fake_rules_list()
    update.new.firewall.append({
        'name': 'bad',
        'type': 'redirect',
        'from': 'missing',
        'to': '@host.lan'
    })
    assert_raises(Exception, firewall.getDeveloperFirewallRules, update)

    # Try something else that we do not recognize.
    update.new.firewall = fake_rules_list()
    update.new.firewall.append({
        'name': 'bad',
        'type': 'redirect',
        'from': 'missing',
        'to': 'missing'
    })
    assert_raises(Exception, firewall.getDeveloperFirewallRules, update)


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
    from paradrop.lib.config import network

    # Test interfaceDefsEqual function
    iface1 = {
        'name': 'mywifi',
        'netType': 'wifi',
        'internalIntf': 'wlan0'
    }
    iface2 = iface1.copy()
    assert network.interfaceDefsEqual(iface1, iface2)
    iface2['internalIntf'] = 'wlan1'
    assert not network.interfaceDefsEqual(iface1, iface2)

    # Test normal case where key is defined and encryption is implied.
    iface = dict()
    cfg = {'key': 'password'}
    network.getWifiKeySettings(cfg, iface)
    assert iface['key'] == "password"

    # Test normal case where encryption is set to "none".
    iface = dict()
    cfg = {'encryption': 'none'}
    network.getWifiKeySettings(cfg, iface)
    assert iface['encryption'] == "none"

    # Test error case where encryption is defined but no key is present.
    iface = dict()
    cfg = {'encryption': 'psk2'}
    assert_raises(Exception, network.getWifiKeySettings, cfg, iface)

    update = MockUpdate()
    update.old = None
    update.new = MockChute()

    # Should do nothing on a chute with no "networkInterfaces" cache key.
    network.reclaimNetworkResources(update.new)

    # Chute has no net information, we should pass silently.
    assert network.getNetworkConfig(update) is None

    update.new.net = {
        'mywifi': {
            'type': 'wifi',
            'intfName': 'wlan0',
            'encryption': 'psk2',
            'key': 'password'
        }
    }

    devices = {
        'wifi': [{'name': 'wlan0'}]
    }
    update.new.setCache("networkDevices", devices)

    # Missing 'ssid' field should raise exception.
    assert_raises(Exception, network.getNetworkConfig, update)

    update.new.net['mywifi']['ssid'] = "Paradrop"

    # Need to make a writable location for our config files.
    settings.UCI_CONFIG_DIR = tempfile.mkdtemp()

    # Try the normal sequence of steps for installing a new chute.
    network.getNetworkConfig(update)
    network.getOSNetworkConfig(update)
    network.getVirtNetworkConfig(update)
    network.setOSNetworkConfig(update)
    network.abortNetworkConfig(update)

    # Set up state so that old chute matches new chute.
    update.old = MockChute()
    update.old.net = update.new.net.copy()
    ifaces = list(update.new.getCache("networkInterfaces"))
    update.old.setCache("networkInterfaces", ifaces)

    # Now try sequence of steps that would occur for a restart.
    network.reclaimNetworkResources(update.old)
    network.getNetworkConfig(update)
    network.getOSNetworkConfig(update)
    network.getVirtNetworkConfig(update)
    network.setOSNetworkConfig(update)

    # Try asking for a new chute without any interfaces.
    update.new.net = dict()

    # This would be a restart where we remove an interface that was in old but
    # not in new.
    network.getNetworkConfig(update)
    network.getOSNetworkConfig(update)
    network.getVirtNetworkConfig(update)
    network.setOSNetworkConfig(update)
    network.abortNetworkConfig(update)

    # Try a network interface with missing 'type' field.
    update.new.net = {
        'mywifi': {
            'intfName': 'wlan0',
        }
    }
    assert_raises(Exception, network.getNetworkConfig, update)

    # Try asking for something funny.
    update.new.net = {
        'mywifi': {
            'type': 'fail',
            'intfName': 'wlan0',
        }
    }
    assert_raises(Exception, network.getNetworkConfig, update)

    # Clean up our config dir
    pdos.remove(settings.UCI_CONFIG_DIR)


def test_revert_config():
    """
    Test the revertConfig function
    """
    from paradrop.lib.config import osconfig

    # Need to make a writable location for our config files.
    settings.UCI_CONFIG_DIR = tempfile.mkdtemp()

    update = MockUpdate()
    update.old = None
    update.new = MockChute()

    osconfig.revertConfig(update, "network")


def test_uciutils():
    """
    Test UCI utility functions
    """
    from paradrop.lib.config import uciutils

    # Test appendListItem function
    options = dict()
    uciutils.appendListItem(options, "name", "value1")
    uciutils.appendListItem(options, "name", "value2")
    assert options['list']['name'] == ["value1", "value2"]

    # Test setList function
    options = dict()
    uciutils.setList(options, "name", ["value1", "value2"])
    assert options['list']['name'] == ["value1", "value2"]


def test_config_wifi():
    """
    Test paradrop.lib.config.wifi
    """
    from paradrop.lib.config import wifi

    update = MockUpdate()
    update.old = None
    update.new = MockChute()

    # Chute has no net information, we should pass silently.
    assert wifi.getOSWirelessConfig(update) is None

    interfaces = fake_interface_list()
    update.new.setCache('networkInterfaces', interfaces)

    wifi.getOSWirelessConfig(update)

    # Verify the new cache entry
    result = update.new.getCache('osWirelessConfig')
    assert len(result) == 1

    # Need to make a writable location for our config files.
    settings.UCI_CONFIG_DIR = tempfile.mkdtemp()

    wifi.setOSWirelessConfig(update)

    # Clean up our config dir
    pdos.remove(settings.UCI_CONFIG_DIR)


def test_pool():
    """
    Test resource pool
    """
    from paradrop.lib.config.pool import NetworkPool, NumericPool

    pool = NumericPool(digits=1)
    for i in range(pool.numValues):
        assert pool.next() == i

    # Try releasing and re-acquiring an item.
    pool.release(0)

    # Double release should raise an exception.
    assert_raises(Exception, pool.release, 0)

    # Now try re-acquiring the released item.
    assert pool.next() == 0

    # Double reserve should raise an exception.
    assert_raises(Exception, pool.reserve, 0, strict=True)

    # Pool is exhausted, so should raise an exception.
    assert_raises(Exception, pool.next)

    # Trigger an error state by tell by telling it there is an item available
    # that it will never find (because we did not change the list of possible
    # values).  This should never actually occur; it just exercises our
    # error-checking.
    pool.numValues += 1
    assert_raises(Exception, pool.next)

    # Test an invalid NetworkPool
    #
    # 192.168.1.1/32 is a single host address, so it is not possible to
    # allocate subnets from that.
    assert_raises(Exception, NetworkPool, "192.168.1.1/32")
