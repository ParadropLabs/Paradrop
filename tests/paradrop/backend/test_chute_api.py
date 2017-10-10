import json

from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.backend import chute_api


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
    chute.name = "test"
    chute.version = 5
    chute.environment = {}
    chute.resources = {}

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


@patch("paradrop.backend.chute_api.ChuteContainer")
@patch("paradrop.backend.chute_api.ChuteStorage")
def test_ChuteApi_get_chute(ChuteStorage, ChuteContainer):
    update_manager = MagicMock()
    api = chute_api.ChuteApi(update_manager)

    request = MagicMock()

    container = MagicMock()
    container.getStatus.return_value = "running"
    ChuteContainer.return_value = container

    chute = MagicMock()
    chute.name = "test"
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


def test_ChuteApi_operations():
    update_manager = MagicMock()
    update_manager.assign_change_id.return_value = 1

    api = chute_api.ChuteApi(update_manager)

    body = {
        'config': {}
    }

    request = MagicMock()
    request.content.read.return_value = json.dumps(body)

    functions = [
        api.update_chute,
        api.start_chute,
        api.stop_chute,
        api.delete_chute
    ]
    for func in functions:
        print("Calling ChuteApi {}".format(func.__name__))

        data = func(request, "test")
        assert isinstance(data, basestring)

        result = json.loads(data)
        assert result['change_id'] == 1
