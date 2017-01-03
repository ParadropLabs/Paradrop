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
