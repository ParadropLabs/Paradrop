"""
"""
from paradrop.lib.misc.snapd import SnapdClient


def updateSnap(update):
    client = SnapdClient()
    result = client.updateSnap(update.name, update.data)
    if 'message' in result:
        update.progress(result['message'])
