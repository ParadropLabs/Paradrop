from six.moves.urllib.parse import urlparse

import requests

from .config import PdtoolsConfig
from .token_provider import EnvironmentVariableTokenProvider, SavedTokenProvider, DefaultLoginTokenProvider, LoginPromptTokenProvider


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

    def __init__(self, api_spec, url):
        """
        Initialize AuthenticatedClient object.

        api_spec: specifies the API in use (should be "node" or "cloud")
        """
        self.api_spec = AuthenticatedClient.ApiSpecs[api_spec]

        url_parts = urlparse(url)
        self.auth_domain = url_parts.netloc

        auth_template = self.api_spec['auth_url']
        self.auth_url = auth_template.format(scheme=url_parts.scheme,
                netloc=url_parts.netloc)

        # List of token providers. We will try these in order to obtain a valid
        # auth token in order to fulfill a request. Note that some of these are
        # parameterized based on the API spec. For example, the node and cloud
        # APIs have a different format for the authentication URL.
        self.token_providers = [
            EnvironmentVariableTokenProvider(),
            SavedTokenProvider(self.auth_domain),
            DefaultLoginTokenProvider(self.auth_url, self.api_spec['param_map']),
            LoginPromptTokenProvider(self.auth_url, self.api_spec['param_map'])
        ]

    def login(self):
        config = PdtoolsConfig.load()
        token = config.getAccessToken(self.auth_domain)
        if token is not None:
            return token

        provider = LoginPromptTokenProvider(self.auth_url, self.api_spec['param_map'])
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
            token = config.getAccessToken(self.auth_domain)
            if token is None:
                break
            else:
                config.removeAccessToken(token)
                config.save()
                removed += 1

        return removed

    def request(self, method, url, authenticated=True, json=None, headers=None, data=None, **kwargs):
        session = requests.Session()
        request = requests.Request(method, url, json=json, headers=headers,
                data=data, **kwargs)

        # Extract just the hostname from the controller URL.  This will be the
        # authentication domain.
        url_parts = urlparse(url)

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

            res = session.send(prepped)
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
                    return res.json()
