import json
import os
import tarfile

from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.backend import chute_api
from paradrop.core.auth.user import User
from paradrop.core.chute.chute import Chute


def test_ChuteCacheEncoder():
    obj = {
        'set': set(),
        'key': 'value'
    }

    # Expect a TypeError because set() is not JSON serializable.
    assert_raises(TypeError, json.dumps, obj)

    # Use the ChuteCacheEncoder and then try reloading the object.
    encoded = json.dumps(obj, cls=chute_api.ChuteCacheEncoder)
    result = json.loads(encoded)

    # Expect equality for serializable values.
    assert result['key'] == obj['key']

    # Expect a string from the nonserializable object.
    assert isinstance(result['set'], basestring)


def test_UpdateEncoder():
    update = MagicMock()
    update.createdTime = 0
    update.responses = []
    update.failure = "OK"

    # Use the UpdateEncoder and then try reloading the object.
    encoded = json.dumps(update, cls=chute_api.UpdateEncoder)
    result = json.loads(encoded)

    assert result['created'] == update.createdTime
    assert result['responses'] == update.responses
    assert result['failure'] == update.failure


def test_tarfile_is_safe():
    # MagicMock(name="foo") does not work because the name attribute is
    # reserved.  We need to make the object then set the name attribute.
    # https://bradmontgomery.net/blog/how-world-do-you-mock-name-attribute/
    def make_mock(name):
        x = MagicMock()
        x.name = name
        return x

    # A tar object behaves like a list of objects with name attributes, so we
    # can mock it as a list. These are all safe relative paths.
    tar = [
        make_mock("images/image.jpg"),
        make_mock("Dockerfile"),
        make_mock(".dockerignore"),
        make_mock("silly/../README.md"),
        make_mock("./a/b/c")
    ]
    assert chute_api.tarfile_is_safe(tar)

    # Not safe!
    tar = [
        make_mock("README.md"),
        make_mock("/etc/passwd")
    ]
    assert not chute_api.tarfile_is_safe(tar)

    # Also not safe!
    tar = [
        make_mock("README.md"),
        make_mock("../.ssh/authorized_keys")
    ]
    assert not chute_api.tarfile_is_safe(tar)

    # This one is less obvious because the path does not start with a "/" or
    # "../", but we catch it if we normalize the path.
    tar = [
        make_mock("README.md"),
        make_mock("images/../../.bashrc")
    ]
    assert not chute_api.tarfile_is_safe(tar)


def test_extract_tarred_chute():
    # Normal case: tar file with a paradrop.yaml file.
    with open("/tmp/paradrop.yaml", "w") as output:
        output.write("name: test")

    tar = tarfile.TarFile(name="/tmp/test_chute.tar", mode="w")
    tar.add("/tmp/paradrop.yaml", arcname="paradrop.yaml")
    tar.close()

    with open("/tmp/test_chute.tar", "r") as source:
        workdir, paradrop_yaml = chute_api.extract_tarred_chute(source)
        assert os.path.isdir(workdir)
        assert paradrop_yaml['name'] == "test"

    # Bad case: empty tar file, no paradrop.yaml.
    tar = tarfile.TarFile(name="/tmp/test_chute.tar", mode="w")
    tar.close()

    with open("/tmp/test_chute.tar", "r") as source:
        assert_raises(Exception, chute_api.extract_tarred_chute, source)


@patch("paradrop.backend.chute_api.ChuteContainer")
@patch("paradrop.backend.chute_api.ChuteStorage")
def test_ChuteApi_get_chutes(ChuteStorage, ChuteContainer):
    update_manager = MagicMock()
    api = chute_api.ChuteApi(update_manager)

    request = MagicMock()

    container = MagicMock()
    container.getStatus.return_value = "running"
    ChuteContainer.return_value = container

    storage = MagicMock()
    ChuteStorage.return_value = storage

    chute = MagicMock()
    chute.environment = {}
    chute.name = "test"
    chute.state = "running"
    chute.resources = {}
    chute.version = 5
    chute.get_owner.return_value = "paradrop"

    storage.getChuteList.return_value = [chute]

    data = api.get_chutes(request)
    assert isinstance(data, basestring)

    result = json.loads(data)
    assert result[0]['name'] == chute.name
    assert result[0]['version'] == chute.version


def test_ChuteApi_create_chute():
    update_manager = MagicMock()
    update_manager.assign_change_id.return_value = 1

    api = chute_api.ChuteApi(update_manager)

    body = {
        'config': {}
    }

    request = MagicMock()
    request.content.read.return_value = json.dumps(body)

    data = api.create_chute(request)
    assert isinstance(data, basestring)

    result = json.loads(data)
    assert result['change_id'] == 1

    assert update_manager.add_update.called


@patch("paradrop.backend.chute_api.extract_tarred_chute")
def test_ChuteApi_create_chute_tarfile(extract_tarred_chute):
    update_manager = MagicMock()
    update_manager.assign_change_id.return_value = 1

    api = chute_api.ChuteApi(update_manager)

    request = MagicMock()
    request.requestHeaders.getRawHeaders.return_value = ["application/x-tar"]
    request.user = User.get_internal_user()

    workdir = "/tmp/test"
    paradrop_yaml = {
        'name': 'chute'
    }
    extract_tarred_chute.return_value = (workdir, paradrop_yaml)

    # Case 1: should work normally.
    data = api.create_chute(request)
    assert isinstance(data, basestring)
    result = json.loads(data)
    assert result['change_id'] == 1
    assert update_manager.add_update.called

    # Case 2: deprecated way of declaring name, but should still work.
    workdir = "/tmp/test"
    paradrop_yaml = {
        'config': {
            'name': 'chute'
        }
    }
    extract_tarred_chute.return_value = (workdir, paradrop_yaml)

    data = api.create_chute(request)
    assert isinstance(data, basestring)
    result = json.loads(data)
    assert result['change_id'] == 1
    assert update_manager.add_update.called

    # Case 3: missing name, should raise exception.
    workdir = "/tmp/test"
    paradrop_yaml = {}
    extract_tarred_chute.return_value = (workdir, paradrop_yaml)

    assert_raises(Exception, api.create_chute, request)


@patch("paradrop.backend.chute_api.ChuteContainer")
@patch("paradrop.backend.chute_api.ChuteStorage")
def test_ChuteApi_get_chute(ChuteStorage, ChuteContainer):
    update_manager = MagicMock()
    api = chute_api.ChuteApi(update_manager)

    request = MagicMock()
    request.user = User.get_internal_user()

    container = MagicMock()
    container.getStatus.return_value = "running"
    ChuteContainer.return_value = container

    chute = MagicMock()
    chute.name = "test"
    chute.state = "running"
    chute.version = 5
    chute.environment = {}
    chute.resources = {}

    ChuteStorage.chuteList = {
        "test": chute
    }

    data = api.get_chute(request, chute.name)
    assert isinstance(data, basestring)

    result = json.loads(data)
    assert result['name'] == chute.name
    assert result['version'] == chute.version


@patch("paradrop.backend.chute_api.extract_tarred_chute")
def test_ChuteApi_update_chute_tarfile(extract_tarred_chute):
    update_manager = MagicMock()
    update_manager.assign_change_id.return_value = 1

    api = chute_api.ChuteApi(update_manager)

    request = MagicMock()
    request.requestHeaders.getRawHeaders.return_value = ["application/x-tar"]
    request.user = User.get_internal_user()

    # Case 1: should work normally.
    workdir = "/tmp/test"
    paradrop_yaml = {
        'name': 'chute'
    }
    extract_tarred_chute.return_value = (workdir, paradrop_yaml)

    data = api.update_chute(request, "chute")
    assert isinstance(data, basestring)
    result = json.loads(data)
    assert result['change_id'] == 1
    assert update_manager.add_update.called

    # Case 2: deprecated way of declaring name, but should still work.
    workdir = "/tmp/test"
    paradrop_yaml = {
        'config': {
            'name': 'chute'
        }
    }
    extract_tarred_chute.return_value = (workdir, paradrop_yaml)

    data = api.update_chute(request, "chute")
    assert isinstance(data, basestring)
    result = json.loads(data)
    assert result['change_id'] == 1
    assert update_manager.add_update.called

    # Case 3: missing name, should raise exception.
    workdir = "/tmp/test"
    paradrop_yaml = {}
    extract_tarred_chute.return_value = (workdir, paradrop_yaml)

    assert_raises(Exception, api.update_chute, request, "chute")


def test_ChuteApi_operations():
    update_manager = MagicMock()
    update_manager.assign_change_id.return_value = 1

    api = chute_api.ChuteApi(update_manager)

    body = {
        'config': {}
    }

    request = MagicMock()
    request.content.read.return_value = json.dumps(body)
    request.user = User.get_internal_user()

    functions = [
        api.update_chute,
        api.stop_chute,
        api.start_chute,
        api.restart_chute,
        api.delete_chute
    ]
    for func in functions:
        print("Calling ChuteApi {}".format(func.__name__))

        data = func(request, "test")
        assert isinstance(data, basestring)

        result = json.loads(data)
        assert result['change_id'] == 1


@patch("paradrop.backend.chute_api.ChuteStorage")
def test_ChuteApi_get_chute_cache(ChuteStorage):
    update_manager = MagicMock()
    update_manager.assign_change_id.return_value = 1

    api = chute_api.ChuteApi(update_manager)

    chute = MagicMock()
    chute.getCacheContents.return_value = {}

    ChuteStorage.chuteList = {
        "test": chute
    }

    request = MagicMock()
    request.user = User.get_internal_user()

    result = api.get_chute_cache(request, "test")
    assert result == "{}"


@patch("paradrop.backend.chute_api.ChuteStorage")
def test_ChuteApi_get_networks(ChuteStorage):
    update_manager = MagicMock()
    update_manager.assign_change_id.return_value = 1

    api = chute_api.ChuteApi(update_manager)

    iface = {
        'name': 'vwlan0',
        'type': 'wifi',
        'internalIntf': 'wlan0'
    }

    chute = Chute(name="test")
    chute.setCache("networkInterfaces", [iface])

    ChuteStorage.chuteList = {
        "test": chute
    }

    request = MagicMock()
    request.user = User.get_internal_user()

    result = api.get_networks(request, "test")
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]['name'] == iface['name']
    assert data[0]['type'] == iface['type']
    assert data[0]['interface'] == iface['internalIntf']


@patch("paradrop.backend.chute_api.ChuteStorage")
def test_ChuteApi_get_network(ChuteStorage):
    update_manager = MagicMock()
    update_manager.assign_change_id.return_value = 1

    api = chute_api.ChuteApi(update_manager)

    iface = {
        'name': 'vwlan0',
        'type': 'wifi',
        'internalIntf': 'wlan0'
    }

    chute = Chute(name="test")
    chute.setCache("networkInterfaces", [iface])

    ChuteStorage.chuteList = {
        "test": chute
    }

    request = MagicMock()
    request.user = User.get_internal_user()

    result = api.get_network(request, "test", "nomatch")
    assert result == "{}"

    result = api.get_network(request, "test", "vwlan0")
    data = json.loads(result)
    assert data['name'] == iface['name']
    assert data['type'] == iface['type']
    assert data['interface'] == iface['internalIntf']


class TestChuteApi(object):
    def __init__(self):
        self.update_manager = MagicMock()
        self.update_manager.assign_change_id.return_value = 1

        self.api = chute_api.ChuteApi(self.update_manager)

        self.interface = {
            'name': 'testing',
            'type': 'wifi',
            'internalIntf': 'wlan0',
            'externalIntf': 'vwlan0'
        }

        chute = Chute(name="test")
        chute.setCache("networkInterfaces", [self.interface])
        chute.setCache("externalSystemDir", "/tmp")
        chute.config = {
            "web": {
                "port": 5000
            }
        }

        self.chute = chute

    @patch("paradrop.backend.chute_api.ChuteStorage")
    def test_get_leases(self, ChuteStorage):
        ChuteStorage.chuteList = {
            self.chute.name: self.chute
        }

        request = MagicMock()
        request.user = User.get_internal_user()

        with open("/tmp/dnsmasq-testing.leases", "w") as output:
            output.write("1512058246 00:0d:b9:40:30:80 10.42.0.213 * *")

        result = self.api.get_leases(request, "test", "testing")
        leases = json.loads(result)
        assert len(leases) == 1
        assert leases[0]['mac_addr'] == "00:0d:b9:40:30:80"
        assert leases[0]['ip_addr'] == "10.42.0.213"

    @patch("paradrop.backend.chute_api.hostapd_control.execute")
    @patch("paradrop.backend.chute_api.ChuteStorage")
    def test_get_ssid(self, ChuteStorage, execute):
        ChuteStorage.chuteList = {
            self.chute.name: self.chute
        }
        execute.return_value = "OK"

        request = MagicMock()
        request.user = User.get_internal_user()
        result = self.api.get_ssid(request, self.chute.name, self.interface['name'])
        assert result == "OK"

    @patch("paradrop.backend.chute_api.hostapd_control.execute")
    @patch("paradrop.backend.chute_api.ChuteStorage")
    def test_set_ssid(self, ChuteStorage, execute):
        ChuteStorage.chuteList = {
            self.chute.name: self.chute
        }
        execute.return_value = "OK"

        request = MagicMock()
        request.user = User.get_internal_user()

        body = {}
        request.content.read.return_value = json.dumps(body)

        # Exception: ssid required
        assert_raises(Exception, self.api.set_ssid, request, "test", "testing")

        body = {
            'ssid': 'Free WiFi'
        }
        request.content.read.return_value = json.dumps(body)

        result = self.api.set_ssid(request, self.chute.name, self.interface['name'])
        assert result == "OK"

    @patch("paradrop.backend.chute_api.hostapd_control.execute")
    @patch("paradrop.backend.chute_api.ChuteStorage")
    def test_get_hostapd_status(self, ChuteStorage, execute):
        ChuteStorage.chuteList = {
            self.chute.name: self.chute
        }
        execute.return_value = "OK"

        request = MagicMock()
        request.user = User.get_internal_user()

        result = self.api.get_hostapd_status(request, self.chute.name,
                self.interface['name'])
        assert result == "OK"

    @patch("paradrop.backend.chute_api.subprocess.Popen")
    @patch("paradrop.backend.chute_api.ChuteStorage")
    def test_get_stations(self, ChuteStorage, Popen):
        ChuteStorage.chuteList = {
            self.chute.name: self.chute
        }

        proc = MagicMock()
        Popen.return_value = proc
        proc.stdout = [
            "Station 12:34:56:78:9a:bc (on wlan0)",
            "	inactive time:  304 ms",
            "	rx bytes:       18816",
            "	rx packets:     75",
            "	tx bytes:       5386",
            "	tx packets:     21",
            "	signal:         -29 dBm",
            "	tx bitrate:     54.0 MBit/s"
        ]

        request = MagicMock()
        request.user = User.get_internal_user()

        result = self.api.get_stations(request, self.chute.name,
                self.interface['name'])
        stations = json.loads(result)
        assert len(stations) == 1
        assert stations[0]['mac_addr'] == '12:34:56:78:9a:bc'
        assert stations[0]['rx_bytes'] == '18816'
        assert stations[0]['signal'] == '-29 dBm'
        assert stations[0]['tx_bitrate'] == '54.0 MBit/s'

    @patch("paradrop.backend.chute_api.subprocess.Popen")
    @patch("paradrop.backend.chute_api.ChuteStorage")
    def test_get_station(self, ChuteStorage, Popen):
        ChuteStorage.chuteList = {
            self.chute.name: self.chute
        }

        proc = MagicMock()
        Popen.return_value = proc
        proc.stdout = [
            "Station 12:34:56:78:9a:bc (on wlan0)",
            "	inactive time:  304 ms",
            "	rx bytes:       18816",
            "	rx packets:     75",
            "	tx bytes:       5386",
            "	tx packets:     21",
            "	signal:         -29 dBm",
            "	tx bitrate:     54.0 MBit/s"
        ]

        request = MagicMock()
        request.user = User.get_internal_user()

        result = self.api.get_station(request, self.chute.name,
                self.interface['name'], '12:34:56:78:9a:bc')
        station = json.loads(result)
        assert station['mac_addr'] == '12:34:56:78:9a:bc'
        assert station['rx_bytes'] == '18816'
        assert station['signal'] == '-29 dBm'
        assert station['tx_bitrate'] == '54.0 MBit/s'

    @patch("paradrop.backend.chute_api.subprocess.Popen")
    @patch("paradrop.backend.chute_api.ChuteStorage")
    def test_delete_station(self, ChuteStorage, Popen):
        ChuteStorage.chuteList = {
            self.chute.name: self.chute
        }

        proc = MagicMock()
        Popen.return_value = proc
        proc.stdout = [
            "OK"
        ]

        request = MagicMock()
        request.user = User.get_internal_user()

        result = self.api.delete_station(request, self.chute.name,
                self.interface['name'], '12:34:56:78:9a:bc')
        messages = json.loads(result)
        assert len(messages) == 1
        assert messages[0] == "OK"

    @patch("paradrop.backend.chute_api.WebSocketResource")
    @patch("paradrop.backend.chute_api.ChuteStorage")
    def test_hostapd_control(self, ChuteStorage, WebSocketResource):
        ChuteStorage.chuteList = {
            self.chute.name: self.chute
        }

        request = MagicMock()
        request.user = User.get_internal_user()

        self.api.hostapd_control(request, self.chute.name,
                self.interface['name'])
        WebSocketResource.assert_called()

    @patch("paradrop.backend.chute_api.ChuteStorage")
    def test_set_chute_config(self, ChuteStorage):
        ChuteStorage.chuteList = {
            self.chute.name: self.chute
        }

        request = MagicMock()
        request.user = User.get_internal_user()

        result = self.api.set_chute_config(request, self.chute.name)
        change = json.loads(result)
        assert change['change_id'] == 1
