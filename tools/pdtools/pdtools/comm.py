from __future__ import print_function

import base64
import getpass
import os
from pprint import pprint
from six.moves.urllib.parse import urlparse

import builtins
import requests
import websocket

from .config import PdtoolsConfig


PDSERVER_URL = os.environ.get('PDSERVER_URL', 'https://paradrop.org')

LOCAL_DEFAULT_USERNAME = "paradrop"
LOCAL_DEFAULT_PASSWORD = ""


def change_json(data, path, value):
    """
    Replace a value in a JSON object.
    """
    parts = path.split('.')
    head = data
    for i in range(len(parts)-1):
        if isinstance(head, list):
            parts[i] = int(parts[i])
        head = head[parts[i]]
    head[parts[-1]] = value


class LoginGatherer(object):
    """
    LoginGatherer is an iterator that produces username/password tuples.

    On the first iteration, it returns a default username/password combination
    for convenience. On subsequent iterations, it prompts the user for input.

    The class method prompt() can be used directly in a loop for situations
    where the default is not desired.

    Usage examples:

    for username, password in LoginGatherer(netloc):
        ...

    while True:
        username, password = LoginGatherer.prompt(netloc)
    """
    def __init__(self, netloc):
        self.first = True
        self.netloc = netloc

    def __iter__(self):
        self.first = True
        return self

    def __next__(self):
        if self.first:
            self.first = False
            return (LOCAL_DEFAULT_USERNAME, LOCAL_DEFAULT_PASSWORD)
        else:
            return LoginGatherer.prompt(self.netloc)

    def next(self):
        """
        Get the next username and password pair.
        """
        return self.__next__()

    @classmethod
    def prompt(cls, netloc):
        """
        Prompt the user to enter a username and password.

        The netloc argument is presented in the prompt, so that the user knows
        the relevant authentication domain.
        """
        print("Please enter your username and password for {}."
              .format(netloc))
        username = builtins.input("Username: ")
        password = getpass.getpass("Password: ")
        return (username, password)


def pdserver_request(method, url, json=None, headers=None):
    """
    Issue a Paradrop controller API request.

    This will prompt for a username and password if necessary.
    """
    session = requests.Session()

    # Extract just the hostname from the controller URL.  This will be the
    # authentication domain.
    parts = urlparse(PDSERVER_URL)

    config = PdtoolsConfig.load()
    token = config.getAccessToken(parts.netloc)

    while True:
        while token is None:
            username, password = LoginGatherer.prompt(parts.netloc)
            data = {
                'email': username,
                'password': password
            }

            auth_url = '{}/auth/local'.format(PDSERVER_URL)
            request = requests.Request('POST', auth_url, json=data, headers=headers)
            prepped = session.prepare_request(request)
            res = session.send(prepped)
            print("Server responded: {} {}".format(res.status_code, res.reason))

            try:
                res_data = res.json()
                token = res_data['token']

                config.addAccessToken(parts.netloc, username, token)
                config.save()
            except:
                pass

        session.headers.update({'Authorization': 'Bearer {}'.format(token)})
        request = requests.Request(method, url, json=json, headers=headers)
        prepped = session.prepare_request(request)

        res = session.send(prepped)
        print("Server responded: {} {}".format(res.status_code, res.reason))
        if res.status_code == 401:
            # Token is probably expired.
            config.removeAccessToken(token)
            config.save()
            token = None
            continue
        else:
            return res


def router_login(request_url, username, password, session):
    url_parts = urlparse(request_url)

    auth_url = "{}://{}/api/v1/auth/local".format(url_parts.scheme, url_parts.netloc)
    data = {
        'username': username,
        'password': password
    }
    request = requests.Request('POST', auth_url, json=data)
    prepped = session.prepare_request(request)
    res = session.send(prepped)
    print("Server responded: {} {}".format(res.status_code, res.reason))

    if res.ok:
        data = res.json()
        token = data['token']

        return (res.status_code, token)

    else:
        return (res.status_code, None)


def router_request(method, url, json=None, headers=None, dump=True, data=None, **kwargs):
    """
    Issue a router API request.

    This will prompt for a username and password if necessary.
    """
    session = requests.Session()
    request = requests.Request(method, url, json=json, headers=headers,
            data=data, **kwargs)

    # Extract just the hostname from the controller URL.  This will be the
    # authentication domain.
    url_parts = urlparse(url)

    config = PdtoolsConfig.load()
    token = config.getAccessToken(url_parts.netloc)

    # If data is a file or file-like stream, then every time we read from it,
    # the read pointer moves to the end, and we will need to reset it if we are
    # to read again.
    try:
        pos = data.tell()
    except AttributeError:
        pos = None

    if token is not None:
        session.headers.update({'Authorization': 'Bearer {}'.format(token)})
        prepped = session.prepare_request(request)

        res = session.send(prepped)
        print("Server responded: {} {}".format(res.status_code, res.reason))
        if res.status_code == 401:
            # Token has probably expired.
            config.removeAccessToken(token)
            config.save()
            token = None
        else:
            # Not an auth error, so return the result.
            if res.ok and dump:
                data = res.json()
                pprint(data)
            return res

    for username, password in LoginGatherer(url_parts.netloc):
        # Try to get a token for later use. Prior to 1.10, paradrop-daemon
        # does not not support tokens.
        _, token = router_login(url, username, password, session)
        if token is not None:
            config.addAccessToken(url_parts.netloc, username, token)
            config.save()

        userpass = "{}:{}".format(username, password).encode('utf-8')
        encoded = base64.b64encode(userpass.encode('utf-8')).decode('ascii')
        session.headers.update({'Authorization': 'Basic {}'.format(encoded)})
        prepped = session.prepare_request(request)

        # Reset the read pointer if the body comes from a file.
        if pos is not None:
            prepped.body.seek(pos)

        res = session.send(prepped)
        print("Server responded: {} {}".format(res.status_code, res.reason))
        if res.status_code == 401:
            # Probably incorrect username/password, so try again.
            continue
        else:
            if res.ok and dump:
                data = res.json()
                pprint(data)
            return res


def router_ws_request(url, headers=None, **kwargs):
    """
    Issue a router WS connection.

    This will prompt for a username and password if necessary.
    """
    if headers is None:
        headers = {}
    else:
        headers = headers.copy()

    def on_error(ws, x):
        print(x)

    url_parts = urlparse(url)
    config = PdtoolsConfig.load()
    token = config.getAccessToken(url_parts.netloc)

    if token is not None:
        headers.update({'Authorization': 'Bearer {}'.format(token)})
    else:
        username, password = LoginGatherer.prompt(url_parts.netloc)

        userpass = "{}:{}".format(username, password)
        encoded = base64.b64encode(userpass.encode('utf-8')).decode('ascii')
        headers.update({'Authorization': 'Basic {}'.format(encoded)})

    ws = websocket.WebSocketApp(url, header=headers, **kwargs)
    ws.on_error = on_error
    ws.run_forever()
