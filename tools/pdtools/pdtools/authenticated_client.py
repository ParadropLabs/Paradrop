import os
from six.moves.urllib.parse import urlparse

import requests
import websocket

from . import token_provider
from .config import PdtoolsConfig
from .errors import ParadropConnectionError


PDSERVER_URL = os.environ.get('PDSERVER_URL', 'https://paradrop.org')


def get_controller_domain():
    url_parts = urlparse(PDSERVER_URL)
    return url_parts.netloc


class AuthenticatedClient(object):
    ApiSpecs = {
        "cloud": {
            "auth_failure_codes": set([401]),
            "auth_url": "{scheme}://{netloc}/auth/local",
            "param_map": {
                "username": "email",
                "password": "password"
            }
        },
        "node": {
            "auth_failure_codes": set([401]),
            "auth_url": "{scheme}://{netloc}/api/v1/auth/local",
            "param_map": {
                "username": "username",
                "password": "password"
            }
        }
    }

    # Subclasses can override this to alter connection errors resulting from
    # requests.
    connection_error_type = ParadropConnectionError

    def __init__(self, api_spec, url, debug=False):
        """
        Initialize AuthenticatedClient object.

        api_spec: specifies the API in use (should be "node" or "cloud")
        """
        self.api_spec = AuthenticatedClient.ApiSpecs[api_spec]

        url_parts = urlparse(url)
        self.authority = url_parts.netloc
        self.auth_domain = url_parts.netloc # deprecate: authority is preferred

        auth_template = self.api_spec['auth_url']
        self.auth_url = auth_template.format(scheme=url_parts.scheme,
                netloc=url_parts.netloc)

        # List of token providers. We will try these in order to obtain a valid
        # auth token in order to fulfill a request. Note that some of these are
        # parameterized based on the API spec. For example, the node and cloud
        # APIs have a different format for the authentication URL.
        self.token_providers = [
            token_provider.EnvironmentVariableTokenProvider(),
            token_provider.SavedTokenProvider(self.authority),
            token_provider.DefaultLoginTokenProvider(self.auth_url,
                self.api_spec['param_map']),
            token_provider.LoginPromptTokenProvider(self.auth_url,
                self.api_spec['param_map'])
        ]
        if api_spec == "node":
            provider = token_provider.SavedCloudTokenProvider(
                    "{scheme}://{netloc}/api/v1/auth/cloud".format(
                        scheme=url_parts.scheme,
                        netloc=url_parts.netloc),
                    get_controller_domain())
            self.token_providers.insert(2, provider)

        self.debug = debug

    def login(self):
        for provider in self.token_providers:
            if not provider.is_applicable():
                continue

            token = provider.get_token()
            if token is not None:
                # If the token is non-empty, we assume it must be valid.  Call
                # provider.update to make sure it gets saved.
                provider.update(token, True)
                return token

    def logout(self):
        config = PdtoolsConfig.load()

        # Generally, there should be only zero or one access token, but it is
        # possible for a code bug or other situation to cause there to be multiple
        # tokens.  The loop makes sure we remove them all.
        removed = 0
        while True:
            token = config.getAccessToken(self.authority)
            if token is None:
                break
            else:
                config.removeAccessToken(token)
                config.save()
                removed += 1

        return removed

    def request(self, method, url, authenticated=True, json=None, headers=None, data=None, **kwargs):
        if self.debug:
            print("{} {}".format(method, url))
            if json is not None:
                print(json)

        session = requests.Session()
        request = requests.Request(method, url, json=json, headers=headers,
                data=data, **kwargs)

        # If data is a file or file-like stream, then every time we read from it,
        # the read pointer moves to the end, and we will need to reset it if we are
        # to read again.
        try:
            pos = data.tell()
        except AttributeError:
            pos = None

        # Non-authenticated calls (e.g. to register an account) can bypass the
        # token provider logic.
        if not authenticated:
            prepped = session.prepare_request(request)
            res = session.send(prepped)
            try:
                return res.json()
            except:
                return None

        for provider in self.token_providers:
            if not provider.is_applicable():
                continue

            token = provider.get_token()
            session.headers.update({'Authorization': 'Bearer {}'.format(token)})
            prepped = session.prepare_request(request)

            # Reset the read pointer if the body comes from a file.
            if pos is not None:
                prepped.body.seek(pos)

            try:
                res = session.send(prepped)
            except requests.exceptions.ConnectionError as error:
                raise self.connection_error_type(error.message, error.request,
                        self.authority)

            if res.status_code in self.api_spec['auth_failure_codes']:
                # The status code indicates an authorization failure.  That
                # could mean the token is expired, the password is incorrect,
                # etc.
                provider.update(token, False)
            else:
                provider.update(token, True)
                if res.status_code == 204:
                    return None
                else:
                    try:
                        return res.json()
                    except ValueError:
                        return {"message": res.content}

    def ws_request(self, url, headers=None, **kwargs):
        if self.debug:
            print("Open {}".format(url))

        if headers is None:
            headers = {}
        else:
            headers = headers.copy()

        def on_error(ws, x):
            ws.error = x

        for provider in self.token_providers:
            if not provider.is_applicable():
                continue

            token = provider.get_token()
            headers.update({'Authorization': 'Bearer {}'.format(token)})

            ws = websocket.WebSocketApp(url, header=headers, **kwargs)
            ws.error = None
            ws.on_error = on_error
            ws.run_forever()

            if ws.error is None:
                # Websocket connection was terminated cleanly.
                break
            elif isinstance(ws.error, KeyboardInterrupt):
                # User used Ctrl+C to terminate the session.
                break
