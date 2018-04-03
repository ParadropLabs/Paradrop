#
# This module is DEPRECATED and should be removed prior to the 1.0 release.
#
# Most functionality has been moved to the AuthenticatedClient base class along
# with the ParadropClient and ControllerClient child classes. Some of the old
# command trees (device, group, routers) still depend on the functions in this
# module, and in particular, we should keep the "device" command tree around
# until the 1.0 release because the router_request function here supports
# Paradrop versions prior to 0.10.
#

from __future__ import print_function

import base64
import os
from pprint import pprint
from six.moves.urllib.parse import urlparse

import requests
import websocket

from .config import PdtoolsConfig
from .util import LoginGatherer


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


def router_login(base_url):
    """
    Prompt for router username and password and attempt login.

    Returns the username if successful or None.
    """
    config = PdtoolsConfig.load()
    session = requests.Session()
    url_parts = urlparse(base_url)

    for username, password in LoginGatherer(url_parts.netloc):
        # Try to get a token for later use. Prior to 1.10, paradrop-daemon
        # does not not support tokens.
        _, token = send_router_login(base_url, username, password, session)
        if token is not None:
            config.addAccessToken(url_parts.netloc, username, token)
            config.save()
            return username

    return None


def router_logout(base_url):
    """
    Delete access token(s) for device if they exist.

    Returns the number of tokens removed.
    """
    config = PdtoolsConfig.load()
    url_parts = urlparse(base_url)

    # Generally, there should be only zero or one access token, but it is
    # possible for a code bug or other situation to cause there to be multiple
    # tokens.  The loop makes sure we remove them all.
    removed = 0
    while True:
        token = config.getAccessToken(url_parts.netloc)
        if token is None:
            break
        else:
            config.removeAccessToken(token)
            config.save()
            removed += 1

    return removed


def send_router_login(request_url, username, password, session):
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
        # Try to get a token for later use. Prior to 0.10, paradrop-daemon
        # does not not support tokens.
        _, token = send_router_login(url, username, password, session)
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
