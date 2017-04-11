from mock import patch, MagicMock

from paradrop.backend import auth

def test_parse_credential():
    userpass = 'cGFyYWRyb3A6'
    user_name, password = auth.get_username_password(userpass)
    assert user_name == 'paradrop'
    assert password == ''

    userpass = 'cGFyYWRyb3A6aGVsbG93b3JsZA=='
    user_name, password = auth.get_username_password(userpass)
    assert user_name == 'paradrop'
    assert password == 'helloworld'
