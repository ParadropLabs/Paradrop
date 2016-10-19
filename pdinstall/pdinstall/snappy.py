from __future__ import print_function

import os
import re
import shutil
import subprocess
import urllib


SNAP_FILENAME_RE = re.compile("(\S+)_(\S+)_(\S+).snap")


class Snap(object):
    def __init__(self, source):
        self.source = source
        self.path, self.filename = os.path.split(source)

        match = SNAP_FILENAME_RE.match(self.filename)
        if match is None:
            raise Exception("Snap filename ({}) not in expected format"
                            .format(self.filename))
        else:
            self.name, self.version, self.arch = match.groups()

    def __str__(self):
        return "{}_{}".format(self.name, self.version)

    def getFile(self):
        """
        Downloads the file (if necessary) and makes sure it exists.
        """
        if self.source.startswith("http"):
            self.path = "/tmp"

            print("Downloading {}...".format(self.source))
            dest = os.path.join(self.path, self.filename)
            urllib.urlretrieve(self.source, dest)
            self.source = dest

        return os.path.isfile(self.source)

    def isInstalled(self, ignoreVersion=False):
        """
        Check if this snap is installed.

        If ignoreVersion is True, will check if any version of the snap name is
        installed.
        """
        if ignoreVersion:
            return isInstalled(self.name)
        else:
            return isInstalled(self.name, self.version)


def callSnappy(command, *args, **kwargs):
    """
    Call a snappy command.

    Commands that work with this function are "install", "remove", and "purge".

    Returns True/False indicating success or failure.
    """
    progress = kwargs.get('progress', print)

    cmd = ["snappy", command]
    if command == "install":
        cmd.append("--allow-unauthenticated")
    cmd.extend(args)

    progress("Call: {}".format(" ".join(cmd)))
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
    except Exception as e:
        progress('Warning: "snappy {}" command failed: {}'.format(
              command, e))
        return False

    for line in proc.stdout:
        progress(" . " + line.rstrip())
    for line in proc.stderr:
        progress(" ! " + line.rstrip())

    proc.wait()
    progress("Command returned: {}".format(proc.returncode))
    return proc.returncode == 0


def installSnap(snap, progress=print):
    """
    Install a snap.

    Returns True/False to indicate success/failure.
    """

    # If we are changing from one version to another, and the data directory
    # does not already exist, then Snappy will copy data from the running
    # version to the newly installed version.  We make sure that will happen by
    # deleting the data directory if it already exists, but we do not want to
    # do that if re-installing the same version.
    if not snap.isInstalled() and snap.isInstalled(ignoreVersion=True):
        dataDir = "/var/lib/apps/{}/{}".format(snap.name, snap.version)
        if os.path.exists(dataDir):
            shutil.rmtree(dataDir)

    if not callSnappy("install", snap.source, progress=progress):
        return False

    # We use ignoreVersion here because `snappy list` returns a random string
    # for the version, so we cannot check against the version string in
    # the snap file name.
    return snap.isInstalled(ignoreVersion=True)


def parseSnappyList(source):
    """
    Parse output of 'snappy list' to find versions of installed snaps.

    Returns dictionary mapping snap name to the version installed, e.g.
    {"paradrop": "0.1.0"}.
    """
    snaps = dict()

    firstLine = True
    for line in source:
        if firstLine:
            # TODO: What if snappy changes its output?
            headers = line.split()
            firstLine = False

        else:
            fields = line.split()
            if len(fields) < 3:
                continue

            name = fields[0]
            version = fields[2]
            snaps[name] = version

    return snaps


def installedSnaps():
    """
    Get versions of installed snaps.

    Returns dictionary mapping snap name to the version installed, e.g.
    {"paradrop": "0.1.0"}.
    """
    snaps = dict()

    cmd = ["snappy", "list"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    except Exception as e:
        raise Exception('"snappy list" command failed: {}'.format(e))

    return parseSnappyList(proc.stdout)


def isInstalled(name, version=None):
    """
    Check if snap is installed.

    If version is None, check by name only; otherwise, check that the specified
    version is installed.
    """
    snaps = installedSnaps()
    if name not in snaps:
        return False
    return (version is None or version == snaps[name])
