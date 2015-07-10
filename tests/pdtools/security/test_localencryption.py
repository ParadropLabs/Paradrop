import pdserver.security.localencryption as local


def testPasswordEncrypts():
    password = '123445678'
    hashed = local.hashPassword(password)

    print hashed
    assert hashed != password


def testPasswordRecoverable():
    password = '123445678'
    hashed = local.hashPassword(password)

    assert local.checkPassword(password, hashed)
