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
