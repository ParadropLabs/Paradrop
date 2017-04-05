import base64
import functools

from paradrop.core.chute.chute_storage import ChuteStorage


# TODO: Configurable username/password.
# TODO: Segment permissions based on roles.
#       Admin can do anything, but maybe a guest can still view device status.
#       Chutes should not be able to manipulate other chutes.


def get_allowed_basic():
    """
    Return allowed credentials for Basic authorization.

    This is currently just a proof of concept.  The password needs to be
    configurable.

    Please note: username and password can either be presented in plain text
    such as "admin:password" or base64 encoded such as "YWRtaW46cGFzc3dvcmQ=".
    Both forms should be returned from this function.
    """
    allowed = [
        "admin:password",
        base64.b64encode("admin:password")
    ]
    return set(allowed)


def get_allowed_bearer():
    """
    Return set of allowed bearer tokens.
    """
    allowed = set()

    chuteStore = ChuteStorage()
    chutes = chuteStore.getChuteList()
    for chute in chutes:
        token = chute.getCache('apiToken')
        if token is not None:
            allowed.add(token)

    return allowed


def check_auth(auth_header):
    parts = auth_header.split()
    if parts[0] == "Basic":
        userpass = parts[1]
        return userpass in get_allowed_basic()
    elif parts[0] == "Bearer":
        # Consider using JWT to avoid needing to gather a list of tokens.
        # However, then we need to generate and store a private key.
        token = parts[1]
        return token in get_allowed_bearer()

    return False


def requires_auth(func):
    """
    Use as a decorator for API functions to require authorization.

    This checks the Authorization HTTP header.  It handles username and
    password as well as bearer tokens.
    """
    @functools.wraps(func)
    def decorated(self, request, *args, **kwargs):
        auth_header = request.getHeader('Authorization')
        if not auth_header or not check_auth(auth_header):
            request.setResponseCode(401)
            request.setHeader("WWW-Authenticate", "Basic realm=\"Login Required\"")
            return
        return func(self, request, *args, **kwargs)
    return decorated
