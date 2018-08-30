"""
The TokenProvider abstraction allows for different methods of acquiring a token
for authorization with an HTTP service. As shown in the table below, multiple
methods of acquiring a token are generally available, but their applicability
depends on whether the code is running interactively or inside a chute where
there is no user input and whether the target API is the node or the cloud
controller.  This creates a fair bit of complexity for the AuthenticatedClient
to perform an authenticated API call.

Method               | Caller    | Target API
(x = applicable)     | CLI Chute | Node Cloud
---------------------------------------------
Environment variable | x   x     | x    -
Saved locally        | x   -     | x    x
Saved cloud token    | x   -     | x    -
Default password     | x   -     | x    -
Prompt for input     | x   -     | x    x

Here is an example flow for the more complicated case, interacting with a
node's API:

1. We check for an environment variable because chutes authenticate using
   a token provided through the PARADROP_API_TOKEN variable.
2. We check for a token saved to a file. We save tokens locally so that
   users do not need to type their password with each command.
3. If there is not a saved token or if the saved token has expired, then
   we can try a default password. Most nodes intended for development
   or education purposes retain their default settings.
4. Finally, if user input is available, we can prompt the user to enter
   a username and password. We should generally never prompt for a
   password in code that runs inside a chute. That code is presumed to
   be non-interactive, and it would be better just to return an error.

The TokenProvider abstraction helps simplify the logic above.  It allows an
AuthenticatedClient implementation to instantiate one or more parameterized
TokenProvider objects. With a list of provider objects, the sequence of steps
above amounts to iterating the list and calling `get_token` on each provider
until one of them succeeds.
"""

import getpass
import os
import sys

from six.moves.urllib.parse import urlparse

import builtins
import requests

from .config import PdtoolsConfig


class TokenProvider(object):
    """
    Abstract class for methods that provide authentication tokens.
    """
    def get_token(self):
        return NotImplemented

    def is_applicable(self):
        return False

    def should_retry(self):
        return False

    def update(self, token, success):
        pass


class EnvironmentVariableTokenProvider(TokenProvider):
    """
    Get a token from an environment variable.
    """
    def __init__(self, variable="PARADROP_API_TOKEN"):
        self.variable = variable

    def get_token(self):
        return os.environ.get(self.variable, None)

    def is_applicable(self):
        return self.variable in os.environ


class SavedTokenProvider(TokenProvider):
    """
    Get a token that was saved to a file.
    """
    def __init__(self, domain):
        self.domain = domain

    def get_token(self):
        config = PdtoolsConfig.load()
        return config.getAccessToken(self.domain)

    def is_applicable(self):
        return True

    def update(self, token, success):
        if not success:
            config = PdtoolsConfig.load()
            config.removeAccessToken(token)
            config.save()


class SavedCloudTokenProvider(TokenProvider):
    """
    Use a cloud token to attempt authentication with a node.
    """
    def __init__(self, auth_url, domain):
        self.auth_url = auth_url
        self.domain = domain

    def get_token(self):
        config = PdtoolsConfig.load()
        cloud_token = config.getAccessToken(self.domain)
        data = {
            "token": cloud_token
        }

        res = requests.post(self.auth_url, json=data)
        try:
            data = res.json()
            self.token = data['token']
            self.username = data['username']
            return self.token
        except:
            return None

    def is_applicable(self):
        return True

    def update(self, token, success):
        if success and token == self.token:
            url_parts = urlparse(self.auth_url)
            config = PdtoolsConfig.load()
            config.addAccessToken(url_parts.netloc, self.username, token)
            config.save()


class DefaultLoginTokenProvider(TokenProvider):
    """
    Attempt login with a default username and password.
    """
    def __init__(self, auth_url, param_map):
        self.auth_url = auth_url
        self.param_map = param_map

    def get_token(self):
        data = {
            self.param_map['username']: 'paradrop',
            self.param_map['password']: ''
        }
        res = requests.post(self.auth_url, json=data)
        try:
            data = res.json()
            return data['token']
        except:
            return None

    def is_applicable(self):
        return True


class LoginPromptTokenProvider(TokenProvider):
    """
    Prompt the user for username and password.
    """
    def __init__(self, auth_url, param_map):
        self.auth_url = auth_url
        self.param_map = param_map

        self.username = None
        self.token = None

    def get_token(self):
        url_parts = urlparse(self.auth_url)

        print("Attempting to log in to authentication domain {}".format(url_parts.netloc))
        self.username = builtins.input("Username: ")
        password = getpass.getpass("Password: ")

        data = {
            self.param_map['username']: self.username,
            self.param_map['password']: password
        }
        res = requests.post(self.auth_url, json=data)
        try:
            data = res.json()
            self.token = data['token']
            return self.token
        except:
            return None

    def is_applicable(self):
        # Not sure if this works. The intent is to prompt for a password if
        # called from the command line but skip this method if running inside a
        # chute.
        return sys.stdin.isatty()

    def update(self, token, success):
        if success and token == self.token:
            url_parts = urlparse(self.auth_url)
            config = PdtoolsConfig.load()
            config.addAccessToken(url_parts.netloc, self.username, token)
            config.save()
