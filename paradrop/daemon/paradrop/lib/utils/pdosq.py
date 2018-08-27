"""
Quiet pdos module.
Implements utility OS operations without relying on the output module.
Therefore, this module can be used by output without circular dependency.
"""

import errno
import os


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
        # EEXIST is fine (directory already existed).  Anything else would be
        # problematic.
        if e.errno != errno.EEXIST:
            raise e
    return False


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
