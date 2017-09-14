import base64
import functools

from paradrop.base.output import out
from paradrop.core.chute.chute_storage import ChuteStorage

# TODO: Configurable username/password.
# TODO: Segment permissions based on roles.
#       Admin can do anything, but maybe a guest can still view device status.
#       Chutes should not be able to manipulate other chutes.


def get_username_password(userpass):
    """
    Please note: username and password can either be presented in plain text
    such as "admin:password" or base64 encoded such as "YWRtaW46cGFzc3dvcmQ=".
    Both forms should be returned from this function.
    """
    plaintext = base64.b64decode(userpass)

    segments = plaintext.split(':')
    count = len(segments)
    if count == 1:
        return segments[0], ''
    elif count == 2:
        return segments
    else:
        raise Execption('There should be at most two segments!')


def verify_password(password_manager, userpass):
    user_name, password = get_username_password(userpass)
    return password_manager.verify_password(user_name, password)


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


def check_auth(password_manager, auth_header):
    parts = auth_header.split()
    if parts[0] == "Basic":
        userpass = parts[1]
        return verify_password(password_manager, userpass)
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
        if not auth_header or not check_auth(self.password_manager, auth_header):
            out.warn('Failed to authenticate')
            request.setResponseCode(401)
            request.setHeader("WWW-Authenticate", "Basic realm=\"Login Required\"")
            return
        return func(self, request, *args, **kwargs)
    return decorated
