# import pdtools.security.localencryption as local
from paradrop.base.lib import crypto


def testPasswordEncrypts():
    password = '123445678'
    hashed = crypto.hashPassword(password)

    print hashed
    assert hashed != password


def testPasswordRecoverable():
    password = '123445678'
    hashed = crypto.hashPassword(password)

    assert crypto.checkPassword(password, hashed)
