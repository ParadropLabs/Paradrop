"""
"""

from paradrop.lib import pdinstall
from paradrop.lib.reporting import getPackageVersion


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

    pdinstall.sendCommand('install', data)
