import binascii
import jwt
import os
import time

from paradrop.base import nexus


def generate_jwt_secret():
    # 32 bytes = 256 bits, recommended key length for HS256.
    material = os.urandom(32)
    return binascii.b2a_hex(material)


class TokenManager(object):
    # Inherit this exception class so that callers can use it without depending
    # on the jwt library.
    InvalidTokenError = jwt.exceptions.InvalidTokenError

    def __init__(self):
        self.secret = nexus.core.getKey('jwt-secret')
        if self.secret is None:
            self.secret = generate_jwt_secret()
            nexus.core.saveKey(self.secret, 'jwt-secret')

    def decode(self, token):
        """
        Decode a JWT that was issued by us.

        Throws an InvalidTokenError on decoding failure or token expiration.
        """
        return jwt.decode(token, self.secret, algorithms=['HS256'])

    def issue(self, subject, expires=2592000, **claims):
        """
        Issue a signed token.

        The subject is mandatory and sets the JWT "sub" claim.  The expiration
        time can be None (no expiration) or a time in seconds from the issue
        time after which the token will expire.  The default is 30 days
        (2592000 seconds).
        """
        data = claims
        data['iat'] = int(time.time())
        data['iss'] = nexus.core.info.pdid
        data['sub'] = subject
        if expires is not None:
            data['exp'] = int(time.time()) + expires
        return jwt.encode(data, self.secret, algorithm='HS256')
