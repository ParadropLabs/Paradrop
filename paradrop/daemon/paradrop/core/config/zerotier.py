import httplib
import json
import os
import subprocess

from paradrop.base.output import out
from paradrop.lib.misc.snapd import SnapdClient
from paradrop.lib.utils import datastruct


def configure(update):
    hostConfig = update.new.getCache('hostConfig')

    snapd = SnapdClient()

    enabled = datastruct.getValue(hostConfig, "zerotier.enabled", False)
    if enabled:
        # TODO: Fix race conditions!  installSnap, updateSnap, and connect are
        # all asynchronous, so they need to be chained properly.
        if not os.path.exists("/snap/zerotier-one"):
            snapd.installSnap('zerotier-one')

        snapd.updateSnap('zerotier-one', {'action': 'enable'})

        # These interfaces are not automatically connected, so take care of that.
        snapd.connect('zerotier-one', 'network-control', 'core',
                'network-control')
        snapd.connect('paradrop-daemon', 'zerotier-control', 'zerotier-one',
                'zerotier-control')

        networks = datastruct.getValue(hostConfig, "zerotier.networks", [])
        for network in set(networks):
            join_network(network)

    else:
        # Disable the zerotier service.
        snapd.updateSnap('zerotier-one', {'action': 'disable'})


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


def join_network(nwid):
    conn = httplib.HTTPConnection("localhost", 9993)
    path = "/network/{}".format(nwid)
    body = "{}"
    headers = {
        "Content-Type": "application/json",
        "X-ZT1-Auth": get_auth_token()
    }
    conn.request("POST", path, body, headers)
    res = conn.getresponse()
    data = json.loads(res.read())
    return data
