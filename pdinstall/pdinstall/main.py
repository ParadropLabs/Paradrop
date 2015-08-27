import argparse
import os
import re
import subprocess

from . import snappy


SERVICE_FILES_DIR = '/etc/systemd/system/'


def getArgs(argv=None):
    parser = argparse.ArgumentParser(description='Paradrop installer')
    parser.add_argument('source', type=str,
                        help='Source (file path or URL)')
    parser.add_argument('-f', '--fallback', type=str, action='append', 
                        default=[],
                        help='Fallback snap (file path or URL)')
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


def getSnaps(args):
    """
    Get an ordered list of snaps to try installing.

    Returns an empty list if any of the requested snaps cannot be found.
    """
    snapList = list()
    snapList.append(snappy.Snap(args.source))
    for fallback in args.fallback:
        snapList.append(snappy.Snap(fallback))

    # First make sure we can find all of the snap files.  We do not want to
    # start installing unless we are sure the fallback snaps are available.
    for snap in snapList:
        if not snap.getFile():
            print("Could not find snap file: {}".format(snap.source))

            # Relative paths do not always work on Snappy, so give a helpful
            # hint to the user.
            if not snap.source.startswith("http") and \
                    not snap.source.startswith("/"):
                print("Try giving an absolute path to the snap file.")
            return []

    return snapList


def installFromList(snaps, args):
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
        if not args.ignore_version:
            if snap.isInstalled():
                print('The snap ({}) is already installed.'.format(str(snap)))
                return True

        if snappy.installSnap(snap):
            print('The snap ({}) was successfully installed.'
                    .format(str(snap)))
            return True

        cleanupServiceFiles(snap.name)

    print('No version could be installed.')
    return False


def main():
    args = getArgs()

    snaps = getSnaps(args)
    if installFromList(snaps, args):
        return 0
    else:
        return 1
