##################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
    This file contains any settings required by ANY and ALL modules of the paradrop system.
    They are defaulted to some particular value and can be called by any module in the paradrop
    system with the following code:

        from paradrop import settings
        print(settings.STUFF)

    These settings can be overriden by a KYE:VALUE array

    If settings need to be changed, they should be done so by the initialization code
    (such as pdfcd, pdapi_server, pdfc_config, etc...)

    This is done by calling the following function:
        settings.updateSettings(settings_array)
"""

import os
import re
import sys

DEBUG_MODE = False
# VERBOSE = False

#
# pdserver
#
PDSERVER_URL = "https://paradrop.org"
PDSERVER_MAX_CONCURRENT_REQUESTS = 2

#
# pdfcd
#
PDFCD_PORT = 14321
PDFCD_HEADER_VALUE = "*"
DBAPI_FAILURE_THRESH = float("inf")

#
# fc
#
FC_BOUNCE_UPDATE = None

FC_CHUTESTORAGE_SAVE_PATH = "~/.paradrop/chutes"
FC_CHUTESTORAGE_SAVE_TIMER = 60
RESERVED_CHUTE = "__PARADROP__"

#
# local portal
#
PORTAL_SERVER_PORT = 80

#
# Host configuration file
#
HOST_CONFIG_PATH = "~/.paradrop/hostconfig.yaml"

HOST_DATA_PARTITION = "/writable"

#
# UCI configuration files
#
UCI_CONFIG_DIR = "~/.paradrop/config.d"
UCI_BACKUP_DIR = "~/.paradrop/config-backup.d"

#
# Chute data directory is used to provide persistence for chute data.
# The developer can store files here and they will persist across chute
# updates and restarts (but not uninstallation).
#
# Note: we do not want this in SNAP_APP_DATA_PATH because that path
# contains the snap version.  We want this path to stay constant across
# paradrop upgrades because chutes will have volumes mounted here.
#
# Internal is inside the chute; external is in the host.
#
INTERNAL_DATA_DIR = "/data"
EXTERNAL_DATA_DIR = "~/.paradrop/{chute}"
#
# System directory is used to share system information from the host
# down to the chute such as a list of devices connected to WiFi.  This
# is mounted read-only inside the chute.
#
# Internal is inside the chute; external is in the host.
#
INTERNAL_SYSTEM_DIR = "/paradrop"
EXTERNAL_SYSTEM_DIR = "/var/run/paradrop/system/{chute}"

#
# Username and password to access the private registry.
#
# TODO: The router should receive credentials from pdserver or use something
# unique like its API key.
#
REGISTRY_USERNAME = "routers"
REGISTRY_PASSWORD = "zai7geigh0ujahQu"

#
# pdconfd
#
# PDCONFD_WRITE_DIR: Directory where automatically generated config files
# (dnsmasq.conf) will be stored.  It is better to put it in /var/run because
# /tmp is sandboxed on Snappy.
PDCONFD_WRITE_DIR = '/var/run/pdconfd'

PDCONFD_ENABLED = True

# Pool of address available for chutes that request dynamic addresses.
DYNAMIC_NETWORK_POOL = "192.168.128.0/17"

# Directory containing "docker" binary.
DOCKER_BIN_DIR = "/apps/bin"

###############################################################################
# Helper functions
###############################################################################


def parseValue(key):
    """
    Attempts to parse the key value, so if the string is 'False' it will parse a boolean false.

    :param key: the key to parse
    :type key: string

    :returns: the parsed key.
    """
    # Is it a boolean?
    if(key == 'True' or key == 'true'):
        return True
    if(key == 'False' or key == 'false'):
        return False

    # Is it None?
    if(key == 'None' or key == 'none'):
        return None

    # Is it a float?
    if('.' in key):
        try:
            f = float(key)
            return f
        except:
            pass

    # Is it an int?
    try:
        i = int(key)
        return i
    except:
        pass

    # TODO: check if json

    # Otherwise, its just a string:
    return key

def updateSettings(slist=[]):
    """
    Take a list of key:value pairs, and replace any setting defined.
    Also search through the settings module and see if any matching
    environment variables exist to replace as well.

    :param slist: the list of key:val settings
    :type slist: array.

    :returns: None
    """

    from types import ModuleType
    # Get a handle to our settings defined above
    mod = sys.modules[__name__]

    # Adjust default paths if we are running under ubuntu snappy
    snapDataPath = os.environ.get("SNAP_DATA", None)
    snapCommonPath = os.environ.get("SNAP_COMMON", None)

    if snapDataPath is not None:
        mod.FC_CHUTESTORAGE_SAVE_PATH = os.path.join(snapDataPath, "chutes")
        mod.UCI_CONFIG_DIR = os.path.join(snapDataPath, "config.d")
        mod.UCI_BACKUP_DIR = os.path.join(snapDataPath, "config-backup.d")
        mod.HOST_CONFIG_PATH = os.path.join(snapDataPath, "hostconfig.yaml")

    if snapCommonPath is not None:
        mod.EXTERNAL_DATA_DIR = os.path.join(snapCommonPath,"{chute}")

    # First overwrite settings they may have provided with the arg list
    for kv in slist:
        k, v = kv.split(':', 1)
        # We can either replace an existing setting, or set a new value, we don't care
        setattr(mod, k, parseValue(v))

    # Now search through our settings and look for environment variable matches they defined
    for m in dir(mod):
        a = getattr(mod, m)
        # Look for just variable defs
        if(not hasattr(a, '__call__') and not isinstance(a, ModuleType)):
            if(not m.startswith('__')):
                # Found one of our vars, check environ for a match
                match = os.environ.get(m, None)
                if(match):
                    setattr(mod, m, parseValue(match))
