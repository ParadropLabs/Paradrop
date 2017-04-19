'''
Get system information
'''

import os
import pkg_resources


DMI_FIELDS = [
    "bios_date",
    "bios_vendor",
    "bios_version",
    "product_name",
    "product_serial",
    "product_version",
    "sys_vendor"
]


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


def getDMI():
    """
    Read hardware information from DMI.

    This function attempts to read from known files in /sys/class/dmi/id/.  If
    any are missing or an error occurs, those fields will be omitted from the
    result.

    Returns: a dictionary with fields such as bios_version and product_serial.
    """
    dmi = dict()

    for field in DMI_FIELDS:
        path = os.path.join("/sys/class/dmi/id", field)
        try:
            with open(path, 'r') as source:
                value = source.read().strip()
                dmi[field] = value
        except:
            pass

    return dmi
