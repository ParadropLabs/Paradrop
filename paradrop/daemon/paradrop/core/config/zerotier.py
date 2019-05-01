import errno
import json
import os
import time

from http.client import HTTPConnection

from paradrop.base import settings
from paradrop.base.output import out
from paradrop.lib.utils import datastruct


def wait_for_zerotier(max_delay=120):
    """
    Wait for ZeroTier to start up and create the authtoken file.
    """
    path = os.path.join(settings.ZEROTIER_LIB_DIR, "authtoken.secret")

    if not os.path.isfile(path):
        out.info("Waiting up to {} seconds for ZeroTier authtoken\n".format(max_delay))

    while not os.path.isfile(path):
        time.sleep(1)


def configure(update):
    hostConfig = update.cache_get('hostConfig')

    # Check if ZeroTier is enabled in the node configuration and also whether
    # its data directory exists. We prefer not to wait for it if it is not even
    # installed.
    enabled = datastruct.getValue(hostConfig, "zerotier.enabled", False)
    if enabled and os.path.isdir(settings.ZEROTIER_LIB_DIR):
        new_networks = set(datastruct.getValue(hostConfig,
                "zerotier.networks", []))
        wait_for_zerotier()
    else:
        new_networks = set()

    old_networks = set()
    for network in get_networks(ignore_error=not enabled):
        old_networks.add(network['id'])

    # Leave old networks and join new networks.
    for net in (old_networks - new_networks):
        manage_network(net, action="leave")
    for net in (new_networks - old_networks):
        manage_network(net, action="join")


def getAddress():
    """
    Return the zerotier address for this device or None if unavailable.
    """
    path = os.path.join(settings.ZEROTIER_LIB_DIR, "identity.public")
    try:
        with open(path, "r") as source:
            return source.read().strip()
    except IOError as error:
        if error.errno == errno.ENOENT:
            return None
        else:
            raise


def get_auth_token():
    """
    Return the zerotier auth token for accessing its API or None if unavailable.
    """
    path = os.path.join(settings.ZEROTIER_LIB_DIR, "authtoken.secret")
    try:
        with open(path, "r") as source:
            return source.read().strip()
    except IOError as error:
        if error.errno == errno.ENOENT:
            return None
        else:
            raise


def get_networks(ignore_error=False):
    """
    Get list of active ZeroTier networks.
    """
    auth_token = get_auth_token()
    if auth_token is None:
        return []

    conn = HTTPConnection("localhost", 9993)
    path = "/network"
    headers = {
        "X-ZT1-Auth": auth_token
    }
    conn.request("GET", path, "", headers)
    res = conn.getresponse()
    data = json.loads(res.read())

    # nwid field is deprecated, so make sure id field exists.
    for network in data:
        if 'id' not in network and 'nwid' in network:
            network['id'] = network['nwid']

    return data


def manage_network(nwid, action="join"):
    """
    Join or leave a ZeroTier network.

    nwid: ZeroTier network ID, e.g. "e5cd7a9e1c8a5e83"
    action: either "join" or "leave"
    """
    if action == "join":
        method = "POST"
    elif action == "leave":
        method = "DELETE"
    else:
        raise Exception("Unsupported action: {}".format(action))

    conn = HTTPConnection("localhost", 9993)
    path = "/network/{}".format(nwid)
    body = "{}"
    headers = {
        "Content-Type": "application/json",
        "X-ZT1-Auth": get_auth_token()
    }
    conn.request(method, path, body, headers)
    res = conn.getresponse()
    data = json.loads(res.read())
    return data
