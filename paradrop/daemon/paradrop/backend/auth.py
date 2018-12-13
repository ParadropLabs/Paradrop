import base64
import functools
import json

from klein import Klein
from twisted.internet import defer

from paradrop.base import nexus, settings
from paradrop.base.output import out
from paradrop.core.agent.http import PDServerRequest
from paradrop.core.auth.user import User
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
        raise Exception('There should be at most two segments!')


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


def check_auth(request, password_manager, token_manager):
    auth_header = request.getHeader('Authorization')
    if auth_header is None:
        return False

    parts = auth_header.split()
    if parts[0] == "Basic":
        username, password = get_username_password(parts[1])
        request.user = User(username, "localhost", role="admin")
        return password_manager.verify_password(username, password)
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
            data = token_manager.decode(token)
            domain = data.get("domain", "localhost")
            username = data.get("sub", "paradrop")
            role = data.get("role", "user")
            request.user = User(username, domain, role=role)
            return True
        except token_manager.InvalidTokenError:
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
        if not check_auth(request, self.password_manager, self.token_manager):
            out.info('HTTP {} {} {} {}'.format(request.getClientIP(),
                request.method, request.path, 401))
            request.setResponseCode(401)
            request.setHeader("WWW-Authenticate", "Basic realm=\"Login Required\"")
            return
        return func(self, request, *args, **kwargs)
    return decorated


def verify_cloud_token(token):
    headers = {
        "Authorization": "Bearer {}".format(token)
    }

    # Pass custom Authorization header and setAuthHeader=False to prevent
    # PDServerRequest from using the node's own authorization token.
    request = PDServerRequest("/api/users/me", headers=headers,
            setAuthHeader=False)
    return request.get()


def get_access_level(user, node):
    access_rights = node.get('access_rights', [])

    roles = ["guest"]
    for item in access_rights:
        if item['user_id'] == user['_id']:
            roles.append(item['role'])

    return User.get_highest_role(roles)


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

        # If username is missing in the body, automatically fill in the
        # default.  If password is missing, assume empty string regardless of
        # the default.  The caller can only login without a password if the
        # current password is empty.
        username = body.get('username', settings.DEFAULT_PANEL_USERNAME)
        password = body.get('password', '')

        success = self.password_manager.verify_password(username, password)
        result = {
            'username': username,
            'success': success
        }

        if success:
            token = self.token_manager.issue(username, domain="localhost",
                    role="admin")
            result['token'] = token
        else:
            request.setResponseCode(401)

        return json.dumps(result)

    @routes.route('/cloud', methods=['POST'])
    def auth_cloud(self, request):
        """
        Login using credentials from the cloud controller.

        This is an experimental new login method that lets users
        present a token that they received from the cloud controller
        as a login credential for a node. The idea is to enable easy
        access for multiple developers to share a node, for example,
        during a tutorial.

        Instead of a username/password, the user presents a token received
        from the cloud controller. The verify_cloud_token function
        verifies the validity of the token with the controller, and if
        successful, retrieves information about the bearer, particularly
        the username and role. Finally, we generate a new token that
        enables the user to authenticate with local API endpoints.
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        body = json.loads(request.content.read())
        token = body.get('token', '')

        headers = {
            "Authorization": "Bearer {}".format(token)
        }
        node_id = nexus.core.info.pdid

        # Pass custom Authorization header and setAuthHeader=False to prevent
        # PDServerRequest from using the node's own authorization token.
        d1 = PDServerRequest("/api/users/me",
                headers=headers,
                setAuthHeader=False
            ).get()
        d2 = PDServerRequest("/api/routers/{}".format(node_id),
                headers=headers,
                setAuthHeader=False
            ).get()

        def token_verified(responses):
            for response in responses:
                if not response.success or response.data is None:
                    request.setResponseCode(401)
                    return

            remote_user = responses[0].data
            node_info = responses[1].data

            role = get_access_level(remote_user, node_info)

            token = self.token_manager.issue(remote_user['email'],
                    domain="paradrop.org", role=role)

            result = {
                'token': token,
                'username': remote_user['email']
            }
            return json.dumps(result)

        d = defer.gatherResults([d1, d2])
        d.addCallback(token_verified)
        return d
