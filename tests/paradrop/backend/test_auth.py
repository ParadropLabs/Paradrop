import json
from mock import patch, MagicMock

from paradrop.backend import auth
from paradrop.backend.token_manager import TokenManager


def test_parse_credential():
    userpass = 'cGFyYWRyb3A6'
    user_name, password = auth.get_username_password(userpass)
    assert user_name == 'paradrop'
    assert password == ''

    userpass = 'cGFyYWRyb3A6aGVsbG93b3JsZA=='
    user_name, password = auth.get_username_password(userpass)
    assert user_name == 'paradrop'
    assert password == 'helloworld'


@patch('paradrop.backend.token_manager.nexus')
def test_AuthApi_post_local(nexus):
    nexus.core.info.pdid = "halo42"
    nexus.core.getKey.return_value = "secret"

    password_manager = MagicMock()
    password_manager.DEFAULT_USER_NAME = "paradrop"
    password_manager.DEFAULT_PASSWORD = "password"
    password_manager.verify_password.return_value = True

    token_manager = TokenManager()

    api = auth.AuthApi(password_manager, token_manager)

    request = MagicMock()
    request.content.read.return_value = "{}"

    # verify_password should return True with default username.
    response = api.local_login(request)
    assert isinstance(response, basestring)
    result = json.loads(response)
    assert result['username'] == password_manager.DEFAULT_USER_NAME
    assert result['success'] is True
    assert 'token' in result

    request.content.read.return_value = json.dumps({'username': 'test'})

    # verify_password should return True with test username.
    response = api.local_login(request)
    assert isinstance(response, basestring)
    result = json.loads(response)
    assert result['username'] == 'test'
    assert result['success'] is True
    assert 'token' in result

    # Try decoding the token.
    decoded = token_manager.decode(result['token'])
    assert decoded['sub'] == result['username']
    assert decoded['iss'] == nexus.core.info.pdid

    password_manager.verify_password.return_value = False

    # verify_password should return False.
    response = api.local_login(request)
    assert isinstance(response, basestring)
    result = json.loads(response)
    assert result['success'] is False
    assert result.get('token', None) is None
