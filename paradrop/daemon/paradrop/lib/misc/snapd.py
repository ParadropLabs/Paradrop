import json

from paradrop.base import settings
from paradrop.lib.utils.uhttp import UHTTPConnection


class SnapdClient(object):
    """
    Client for interacting with the snapd API to manage installed snaps.
    """
    def connect(self, plug_snap="paradrop-daemon", plug=None, slot_snap="core", slot=None):
        """
        Connect an interface.
        """
        conn = UHTTPConnection(settings.SNAPD_INTERFACE)
        path = "/v2/interfaces"
        body = json.dumps({
            'action': 'connect',
            'slots': [{'snap': slot_snap, 'slot': slot}],
            'plugs': [{'snap': plug_snap, 'plug': plug}]
        })
        headers = {"Content-type": "application/json"}
        conn.request("POST", path, body, headers)
        res = conn.getresponse()
        data = json.loads(res.read())
        return data['result']

    def installSnap(self, snapName):
        """
        Install a snap from the store.
        """
        conn = UHTTPConnection(settings.SNAPD_INTERFACE)
        path = "/v2/snaps"
        body = json.dumps({
            'action': 'install',
            'snaps': [snapName]
        })
        headers = {"Content-type": "application/json"}
        conn.request("POST", path, body, headers)
        res = conn.getresponse()
        data = json.loads(res.read())
        return data['result']

    def listSnaps(self):
        """
        Get a list of installed snaps.
        """
        conn = UHTTPConnection(settings.SNAPD_INTERFACE)
        conn.request("GET", "/v2/snaps")
        res = conn.getresponse()
        data = json.loads(res.read())
        return data['result']

    def updateSnap(self, snapName, data):
        """
        Post an update to a snap.

        Valid actions are: install, refresh, remove, revert, enable, disable.

        Example:
        updateSnap("paradrop-daemon", {"action": "refresh"}
        """
        conn = UHTTPConnection(settings.SNAPD_INTERFACE)
        path = "/v2/snaps/{}".format(snapName)
        body = json.dumps(data)
        headers = {"Content-type": "application/json"}
        conn.request("POST", path, body, headers)
        res = conn.getresponse()
        data = json.loads(res.read())
        return data['result']
