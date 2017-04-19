from __future__ import print_function

import argparse
import os
import re
import subprocess

from . import snappy
from .progress import ProgressHandler
from .server import CommandServer


SOCKET_ADDRESS = '/var/run/pdinstall.sock'
SERVICE_FILES_DIR = '/etc/systemd/system/'


def getArgs(argv=None):
    parser = argparse.ArgumentParser(description='Paradrop installer')
    parser.add_argument('command', choices=['install', 'server'])
    parser.add_argument('-s', '--source', type=str, action='append', 
                        default=[], dest='sources',
                        help='Snap source (file path or URL)')
    parser.add_argument('-i', '--ignore-version', action="store_true",
                        help='Ignore version check')
    args = parser.parse_args(argv)
    return args


def cleanupServiceFiles(name):
    """
    Clean up service files that will prevent reinstallation.

    This is a workaround for issue ParadropLabs/Paradrop#9.
    """
    for filename in os.listdir(SERVICE_FILES_DIR):
        if filename.startswith(name):
            path = os.path.join(SERVICE_FILES_DIR, filename)
            os.remove(path)


def getSnaps(sources, progress=print):
    """
    Get an ordered list of snaps to try installing.

    Returns an empty list if any of the requested snaps cannot be found.
    """
    snapList = list()
    for source in sources:
        snapList.append(snappy.Snap(source))

    # First make sure we can find all of the snap files.  We do not want to
    # start installing unless we are sure the fallback snaps are available.
    for snap in snapList:
        if not snap.getFile():
            progress("Could not find snap file: {}".format(snap.source))

            # Relative paths do not always work on Snappy, so give a helpful
            # hint to the user.
            if not snap.source.startswith("http") and \
                    not snap.source.startswith("/"):
                progress("Try giving an absolute path to the snap file.")
            return []

    return snapList


def installFromList(snaps, ignoreVersion=False, progress=print):
    """
    Install one of the snaps from a list.

    This function iterates through the list of snaps and returns when 1. it
    successfully installs a snap, 2. it finds that the same version is already
    installed, 3. it reaches the end of the list and none of them succeeded.

    Example:

    Currently installed is paradrop_0.1.0.
    Snap list is paradrop_0.2.0, paradrop_0.1.0.

    installFromList will first try paradrop_0.2.0, and supposing that fails, it
    will move to paradrop_0.1.0.  However, that version is already installed,
    so it will stop there, or if the "--ignore-version" argument was passed, we
    will re-install paradrop_0.1.0.
    """
    for snap in snaps:
        # If the --ignore-version argument was passed, we don't need to check
        # for currently installed version.
        if not ignoreVersion:
            if snap.isInstalled():
                progress('The snap ({}) is already installed.'.format(str(snap)))
                return True

        if snappy.installSnap(snap, progress=progress):
            progress('The snap ({}) was successfully installed.'
                    .format(str(snap)))
            return True

        cleanupServiceFiles(snap.name)

    progress('No version could be installed.')
    return False


def installHandler(data):
    handler = None
    progress = print
    if 'external' in data:
        handler = ProgressHandler(**data['external'])
        progress = handler.write

    snaps = getSnaps(data['sources'], progress=progress)
    success = installFromList(snaps, data.get("ignore-version", False),
            progress=progress)

    if handler is not None:
        handler.complete(success)

    return success


def main():
    args = getArgs()

    if args.command == 'install':
        success = installHandler(vars(args))
        return 0 if success else 1

    elif args.command == 'server':
        server = CommandServer(SOCKET_ADDRESS)
        server.addHandler("install", installHandler)
        server.run()
