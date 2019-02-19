"""
Quiet pdos module.
Implements utility OS operations without relying on the output module.
Therefore, this module can be used by output without circular dependency.
"""
from __future__ import print_function

import errno
import os

from paradrop.lib.utils.yaml import yaml


def makedirs(p):
    """
    Recursive directory creation (like mkdir -p).
    Returns True if the path is successfully created, False if it existed
    already, and raises an OSError on other error conditions.
    """
    try:
        os.makedirs(p)
        return True
    except OSError as e:
        # EEXIST is fine (directory already existed).  We also occasionally get
        # EROFS when making directories in SNAP_COMMON. I am not quite sure
        # what is going on there. Re-raise any other errors.
        if e.errno == errno.EEXIST:
            pass
        elif e.errno == errno.EROFS:
            print("Read-only filesystem error occurred while making {}".format(p))
        else:
            raise e
    return False


def read_yaml_file(path, default=None):
    """
    Read the contents of a file and interpret as YAML.

    default: return value if the file cannot be read.
    """
    try:
        with open(path, "r") as source:
            return yaml.load(source)
    except IOError:
        return default
    except OSError:
        return default


def safe_remove(path):
    """
    Remove a file or silently pass if the file does not exist.

    This function has the same effect as os.remove but suppresses the error if
    the file did not exist. Notably, it must not be used to remove directories.

    Returns True if a file was removed or False if no file was removed.
    """
    try:
        os.remove(path)
        return True
    except OSError as err:
        # Suppress the exception if it is a file not found error.
        # Otherwise, re-raise the exception.
        if err.errno != errno.ENOENT:
            raise

    return False
