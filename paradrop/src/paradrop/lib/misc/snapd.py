import json

from paradrop.base import settings
from paradrop.lib.utils.uhttp import UHTTPConnection


class SnapdClient(object):
    """
    Client for interacting with the snapd API to manage installed snaps.
    """
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
