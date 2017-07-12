import base64
import getpass
import os
from pprint import pprint

import builtins
import requests


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

    username = builtins.input('Username: ')
    password = getpass.getpass('Password: ')
    data = {
        'email': username,
        'password': password
    }

    auth_url = '{}/auth/local'.format(PDSERVER_URL)
    request = requests.Request('POST', auth_url, json=data, headers=headers)
    prepped = session.prepare_request(request)
    res = session.send(prepped)
    res_data = res.json()
    token = res_data['token']

    session.headers.update({'Authorization': 'Bearer {}'.format(token)})
    request = requests.Request(method, url, json=json, headers=headers)
    prepped = session.prepare_request(request)

    res = session.send(prepped)
    print("Server responded: {} {}".format(res.status_code, res.reason))
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
