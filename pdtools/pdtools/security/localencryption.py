'''
Encryption for local use. These functions are shared across multiple libraries.
'''

import bcrypt


def hashPassword(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(str(password), salt)
    return hashed


def checkPassword(raw, hashed):
    ''' Returns true if a hashed password matches a raw one '''
    return bcrypt.hashpw(str(raw), str(hashed)) == hashed
