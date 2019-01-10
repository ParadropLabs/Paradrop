"""
"""
from paradrop.lib.misc.governor import GovernorClient


def updateSnap(update):
    client = GovernorClient()
    result = client.updateSnap(update.name, update.data)
    if 'message' in result:
        update.progress(result['message'])
