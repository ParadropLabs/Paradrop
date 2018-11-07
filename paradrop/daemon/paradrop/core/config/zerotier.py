import httplib
import json
import os

from paradrop.base.output import out
from paradrop.lib.utils import datastruct


def configure(update):
    snap_name = os.environ.get('SNAP_NAME', None)
    if snap_name is None:
        # It seems we are not running as a snap, so this code is not going to
        # work.
        out.info("SNAP_NAME environment variable not found.")
        return

    hostConfig = update.cache_get('hostConfig')

    enabled = datastruct.getValue(hostConfig, "zerotier.enabled", False)
    if enabled:
        new_networks = set(datastruct.getValue(hostConfig,
                "zerotier.networks", []))
    else:
        new_networks = set()

    old_networks = set()
    for network in get_networks():
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
    try:
        with open("/var/snap/zerotier-one/common/identity.public", "r") as source:
            return source.read().strip()
    except:
        return None


def get_auth_token():
    """
    Return the zerotier auth token for accessing its API.
    """
    with open("/var/snap/zerotier-one/common/authtoken.secret", "r") as source:
        return source.read().strip()


def get_networks():
    """
    Get list of active ZeroTier networks.
    """
    conn = httplib.HTTPConnection("localhost", 9993)
    path = "/network"
    headers = {
        "X-ZT1-Auth": get_auth_token()
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

    conn = httplib.HTTPConnection("localhost", 9993)
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
