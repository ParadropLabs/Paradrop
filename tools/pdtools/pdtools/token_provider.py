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
    def __init__(self, variable="PARADROP_API_TOKEN"):
        self.variable = variable

    def get_token(self):
        return os.environ.get(self.variable, None)

    def is_applicable(self):
        return self.variable in os.environ


class SavedTokenProvider(TokenProvider):
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


class DefaultLoginTokenProvider(TokenProvider):
    def __init__(self, auth_url, param_map):
        self.auth_url = auth_url
        self.param_map = param_map

    def get_token(self):
        url_parts = urlparse(self.auth_url)

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
