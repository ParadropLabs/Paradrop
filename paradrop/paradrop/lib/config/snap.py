"""
"""

from paradrop.lib import pdinstall
from paradrop.lib.reporting import getPackageVersion
from paradrop.lib.utils.http import PDServerRequest


def checkVersion(update):
    """
    Check the current version of the snap and block the update if the current
    version is greater or equal to the requested version.
    """
    if update.name != "paradrop":
        raise Exception("This mechanism only works for the paradrop package.")

    version = getPackageVersion("paradrop")
    if version >= update.version:
        raise Exception("Version {} is already installed.".format(version))


def beginInstall(update):
    """
    Begin installation of the snap.

    This function is interesting in that if it succeeds, the running process
    will probably be killed shortly after.
    """
    data = {
        'sources': update.sources
    }

    # If the update came from pdserver, add extra information so that pdinstall
    # will be able to send progress messages back to pdserver.
    if hasattr(update, 'external'):
        # pdinstall will be responsible for reporting when the update is
        # complete.
        update.delegated = True

        external = PDServerRequest.getServerInfo()
        external['update_id'] = update.external['update_id']
        data['external'] = external

    pdinstall.sendCommand('install', data)
