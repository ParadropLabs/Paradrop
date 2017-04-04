import base64
import functools


def get_allowed_basic():
    """
    Return allowed credentials for Basic authorization.

    This is currently just a proof of concept.  The password needs to be
    configurable.

    Please note: username and password can either be presented in plain text
    such as "admin:password" or base64 encoded such as "YWRtaW46cGFzc3dvcmQ=".
    Both forms should be returned from this function.
    """

    # The username and password can be presented in plain text such as
    # "admin:password" or base64 encoded.
    allowed = [
        "admin:password",
        base64.b64encode("admin:password")
    ]
    return set(allowed)


def check_auth(auth_header):
    parts = auth_header.split()
    if parts[0] == "Basic":
        userpass = parts[1]
        return userpass in get_allowed_basic()
    elif parts[0] == "Bearer":
        # TODO: Handle tokens here.
        return False

    return False


def requires_auth(func):
    @functools.wraps(func)
    def decorated(self, request, *args, **kwargs):
        auth_header = request.getHeader('Authorization')
        if not auth_header or not check_auth(auth_header):
            request.setResponseCode(401)
            request.setHeader("WWW-Authenticate", "Basic realm=\"Login Required\"")
            return
        return func(self, request, *args, **kwargs)
    return decorated
