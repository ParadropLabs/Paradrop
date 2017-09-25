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


def pdserver_request(method, url, json=None, headers=None):
    """
    Issue a Paradrop controller API request.

    This will prompt for a username and password if necessary.
    """
    session = requests.Session()

    # Extract just the hostname from the controller URL.  This will be the
    # authentication domain.
    parts = urlparse(PDSERVER_URL)
    host = parts.hostname

    config = PdtoolsConfig.load()
    token = config.getControllerToken(host)

    while True:
        while token is None:
            username = builtins.input("Username: ")
            password = getpass.getpass("Password: ")
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

                config.addControllerToken(host, username, token)
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
            config.removeControllerToken(token)
            config.save()
            token = None
            continue
        else:
            return res


def router_request(method, url, json=None, headers=None, dump=True, **kwargs):
    """
    Issue a router API request.

    This will prompt for a username and password if necessary.
    """
    session = requests.Session()
    request = requests.Request(method, url, json=json, headers=headers, **kwargs)

    # First try with the default username and password.
    # If that fails, prompt user and try again.
    userpass = "{}:{}".format(LOCAL_DEFAULT_USERNAME, LOCAL_DEFAULT_PASSWORD)

    encoded = base64.b64encode(userpass.encode('utf-8')).decode('ascii')
    session.headers.update({'Authorization': 'Basic {}'.format(encoded)})

    prepped = session.prepare_request(request)

    while True:
        res = session.send(prepped)
        print("Router responded: {} {}".format(res.status_code, res.reason))
        if res.status_code == 401:
            username = builtins.input("Username: ")
            password = getpass.getpass("Password: ")
            userpass = "{}:{}".format(username, password).encode('utf-8')
            encoded = base64.b64encode(userpass.encode('utf-8')).decode('ascii')

            session.headers.update({'Authorization': 'Basic {}'.format(encoded)})
            prepped = session.prepare_request(request)

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

    # First try with the default username and password.
    # If that fails, prompt user and try again.
    userpass = "{}:{}".format(LOCAL_DEFAULT_USERNAME, LOCAL_DEFAULT_PASSWORD)
    encoded = base64.b64encode(userpass.encode('utf-8')).decode('ascii')
    headers.update({'Authorization': 'Basic {}'.format(encoded)})

    ws = websocket.WebSocketApp(url, header=headers, **kwargs)
    ws.run_forever()
