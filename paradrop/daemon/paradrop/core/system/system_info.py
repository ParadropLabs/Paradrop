'''
Get system information
'''

import pkg_resources


def getOSVersion():
    """
    Return a string identifying the host OS.
    """
    try:
        with open('/proc/version_signature', 'r') as source:
            return source.read().strip()
    except:
        return None


def getPackageVersion(name):
    """
    Get a python package version.

    Returns: a string or None
    """
    try:
        pkg = pkg_resources.get_distribution(name)
        return pkg.version
    except:
        return None
