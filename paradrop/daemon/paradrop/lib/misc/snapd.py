import json
import os
import time

from paradrop.base import settings
from paradrop.base.output import out
from paradrop.lib.utils.uhttp import UHTTPConnection


SNAP_NAME = os.environ.get('SNAP_NAME', None)


class SnapdClient(object):
    """
    Client for interacting with the snapd API to manage installed snaps.
    """
    def __init__(self, logging=True, wait_async=False):
        """
        Initialize client for interacting with snapd API.

        logging: whether to log results
        wait_async: whether SnapdClient should wait for async calls to finish
        """
        self.logging = True
        self.wait_async = wait_async

    def _maybeWait(self, result):
        """
        Wait for completed result if configured to wait on async calls.
        """
        if result['type'] == 'sync' or not self.wait_async:
            return result['result']

        if result['type'] == 'error':
            result = result['result']
            if self.logging:
                out.warn("snapd error: {}".format(result['message']))
            return result

        while True:
            change = self.get_change(result['change'])
            if change['ready']:
                if self.logging:
                    out.info("{}: {}".format(change['summary'], change['status']))
                return change
            time.sleep(1)

    def connect(self, plug_snap=SNAP_NAME, plug=None, slot_snap="core", slot=None):
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
        return self._maybeWait(data)

    def get_change(self, change_id):
        """
        Get the current status of a change.
        """
        conn = UHTTPConnection(settings.SNAPD_INTERFACE)
        path = "/v2/changes/{}".format(change_id)
        conn.request("GET", path)
        res = conn.getresponse()
        data = json.loads(res.read())
        return self._maybeWait(data)

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
        return self._maybeWait(data)

    def listSnaps(self):
        """
        Get a list of installed snaps.
        """
        conn = UHTTPConnection(settings.SNAPD_INTERFACE)
        conn.request("GET", "/v2/snaps")
        res = conn.getresponse()
        data = json.loads(res.read())
        return self._maybeWait(data)

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
        return self._maybeWait(data)
