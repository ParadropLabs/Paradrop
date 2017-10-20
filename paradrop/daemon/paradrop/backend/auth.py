import base64
import functools
import json

from klein import Klein

from paradrop.base import nexus, settings
from paradrop.base.output import out
from paradrop.core.chute.chute_storage import ChuteStorage
from . import cors

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


def check_auth(password_manager, token_manager, auth_header):
    parts = auth_header.split()
    if parts[0] == "Basic":
        userpass = parts[1]
        return verify_password(password_manager, userpass)
    elif parts[0] == "Bearer":
        token = parts[1]

        # Chutes use non-expiring random tokens that are generated at container
        # creation. This works well because we do not want to deal with
        # expiration or revocation.
        allowed_tokens = get_allowed_bearer()
        if token in allowed_tokens:
            return True

        # Users (through the local portal or pdtools) can acquire expiring
        # JWTs. If the JWT decodes using our secret, then the caller is
        # authenticated.
        #
        # Later on, we may implement tokens issued by paradrop.org but
        # allowing user access to the router, etc. In that case we will
        # need to examine the subject, issuer, and audience claims.
        try:
            decoded = token_manager.decode(token)
            return True
        except token_manager.InvalidTokenError as error:
            pass

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
        if not auth_header or not check_auth(self.password_manager,
                self.token_manager, auth_header):
            out.warn('Failed to authenticate')
            request.setResponseCode(401)
            request.setHeader("WWW-Authenticate", "Basic realm=\"Login Required\"")
            return
        return func(self, request, *args, **kwargs)
    return decorated


class AuthApi(object):
    routes = Klein()

    def __init__(self, password_manager, token_manager):
        self.password_manager = password_manager
        self.token_manager = token_manager

    @routes.route('/local', methods=['POST'])
    def local_login(self, request):
        """
        Login using local authentication (username+password).
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        body = json.loads(request.content.read())
        username = body.get('username', self.password_manager.DEFAULT_USER_NAME)
        password = body.get('password', self.password_manager.DEFAULT_PASSWORD)

        success = self.password_manager.verify_password(username, password)
        result = {
            'username': username,
            'success': success
        }

        if success:
            token = self.token_manager.issue(username)
            result['token'] = token
        else:
            request.setResponseCode(401)

        return json.dumps(result)
