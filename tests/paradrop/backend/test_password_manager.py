from mock import patch, MagicMock
from paradrop.backend import password_manager
from paradrop.base import settings

@patch('paradrop.lib.utils.pdos.write')
@patch('paradrop.lib.utils.pdos.exists')
def test_init_without_password_file(mExists, mWrite):
    mExists.return_value = False
    passwordManager = password_manager.PasswordManager()
    assert passwordManager.password_file == settings.CONFIG_HOME_DIR + 'password'
    mWrite.assert_called_once()
    assert len(passwordManager.records) == 1

@patch('paradrop.lib.utils.pdos.write')
@patch('paradrop.lib.utils.pdos.exists')
@patch('paradrop.lib.utils.pdos.readFile')
def test_init_with_password_file(mReadFile, mExists, mWrite):
    mExists.return_value = True
    mReadFile.return_value = ['paradrop:$6$zwPQnb0CjDMPQ6HH$o564TOpYc9F10Dqmpp6hhGwXaCDKJcixkKxi6BrfrA.KrBE6QPmKaLPkUay9yM.C9cl2gwRYMqJhxiUuMoYgg/']
    passwordManager = password_manager.PasswordManager()
    assert not mWrite.called, 'method should not have been called'
    assert len(passwordManager.records) == 1
    assert passwordManager.records[0]['user_name'] == 'paradrop'
    assert passwordManager.records[0]['password_hash'] == '$6$zwPQnb0CjDMPQ6HH$o564TOpYc9F10Dqmpp6hhGwXaCDKJcixkKxi6BrfrA.KrBE6QPmKaLPkUay9yM.C9cl2gwRYMqJhxiUuMoYgg/'

def test_generate_salt():
    passwordManager = password_manager.PasswordManager()
    salt = passwordManager._generate_salt()
    assert len(salt) == 19
    assert salt.startswith('$6$')

@patch('paradrop.lib.utils.pdos.write')
@patch('paradrop.lib.utils.pdos.exists')
def test_reset(mExists, mWrite):
    mExists.return_value = False
    passwordManager = password_manager.PasswordManager()
    mWrite.assert_called_once()
    mWrite.reset_mock()
    passwordManager.reset()
    mWrite.assert_called_once()

@patch('paradrop.lib.utils.pdos.write')
@patch('paradrop.lib.utils.pdos.exists')
def test_hash_password(mExists, mWrite):
    mExists.return_value = False
    passwordManager = password_manager.PasswordManager()
    password_hash = passwordManager._hash_password('hello');
    assert password_hash.startswith('$6$');
    # 3+1+16+86
    assert len(password_hash) == 106

@patch('paradrop.lib.utils.pdos.write')
@patch('paradrop.lib.utils.pdos.exists')
def test_add_remove_user(mExists, mWrite):
    mExists.return_value = False
    passwordManager = password_manager.PasswordManager()
    mWrite.reset_mock()
    passwordManager.add_user('hello', 'paradrop')
    mWrite.assert_called_once()
    assert len(passwordManager.records) == 2
    mWrite.reset_mock()
    passwordManager.add_user('helloworld', 'paradrop')
    mWrite.assert_called_once()
    assert len(passwordManager.records) == 3
    # Can not add a duplicated user name
    mWrite.reset_mock()
    passwordManager.add_user('hello', 'haha')
    mWrite.assert_not_called()
    assert len(passwordManager.records) == 3

    mWrite.reset_mock()
    passwordManager.remove_user(password_manager.DEFAULT_USER_NAME)
    mWrite.assert_called_once()
    assert len(passwordManager.records) == 2

    mWrite.reset_mock()
    passwordManager.remove_user('notexists')
    mWrite.assert_not_called()
    assert len(passwordManager.records) == 2

@patch('paradrop.lib.utils.pdos.write')
@patch('paradrop.lib.utils.pdos.exists')
def test_verify_password(mExists, mWrite):
    mExists.return_value = False
    passwordManager = password_manager.PasswordManager()

    passwordManager.verify_password(password_manager.DEFAULT_USER_NAME, password_manager.DEFAULT_PASSWORD)

    passwordManager.add_user('hello', 'password!!')
    passwordManager.verify_password('hello', 'password!!')

    passwordManager.add_user('helloworld', 'password!!!')
    passwordManager.verify_password('helloworld', 'password!!!')

@patch('paradrop.lib.utils.pdos.write')
@patch('paradrop.lib.utils.pdos.exists')
def test_change_password(mExists, mWrite):
    mExists.return_value = False
    passwordManager = password_manager.PasswordManager()

    assert passwordManager.verify_password(password_manager.DEFAULT_USER_NAME, password_manager.DEFAULT_PASSWORD)

    assert passwordManager.add_user('hello', 'password!!')
    assert passwordManager.verify_password('hello', 'password!!')

    assert passwordManager.change_password(password_manager.DEFAULT_USER_NAME, 'haha')
    assert not passwordManager.verify_password(password_manager.DEFAULT_USER_NAME, password_manager.DEFAULT_PASSWORD)
    assert passwordManager.verify_password(password_manager.DEFAULT_USER_NAME, 'haha')

    assert passwordManager.change_password('hello', 'heihei')
    assert passwordManager.verify_password('hello', 'heihei')

    assert not passwordManager.change_password('notexists', 'heihei')

    passwordManager.reset()
    assert passwordManager.verify_password(password_manager.DEFAULT_USER_NAME, password_manager.DEFAULT_PASSWORD)
