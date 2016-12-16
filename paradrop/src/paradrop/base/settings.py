##################################################################
# Copyright 2013-2016 All Rights Reserved
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
    (such as pdfcd, pdfc_config, etc...)

    This is done by calling the following function:
        settings.updateSettings(settings_array)
"""

import os
import re
import sys

DEBUG_MODE = False
# VERBOSE = False

HOME_DIR = '/opt/paradrop/'

#
# paths to store daemon related information
#
LOG_DIR = HOME_DIR + 'logs/'
KEY_DIR = HOME_DIR + 'keys/'
MISC_DIR = HOME_DIR + 'misc/'
CONFIG_FILE = HOME_DIR + 'config'

#
# pdserver
#
PDSERVER = "https://paradrop.org"
PDSERVER_MAX_CONCURRENT_REQUESTS = 2
WAMP_ROUTER = "ws://paradrop.org:9086/ws"

#
# pdfcd
#
PDFCD_PORT = 14321
PDFCD_HEADER_VALUE = "*"
DBAPI_FAILURE_THRESH = float("inf")
PDCONFD_WRITE_DIR = "/var/run/pdconfd/"
PDCONFD_ENABLED = True

#
# fc
#
FC_CHUTESTORAGE_FILE = HOME_DIR + "chutes"
FC_CHUTESTORAGE_SAVE_TIMER = 60
FC_BOUNCE_UPDATE = None
RESERVED_CHUTE = "__PARADROP__"
DYNAMIC_NETWORK_POOL = "192.168.128.0/17"

#
# uci
#
UCI_CONFIG_DIR = "/etc/paradrop/config/"
UCI_BACKUP_DIR = "/etc/paradrop/config-backup.d/"

#
# local portal
#
PORTAL_SERVER_PORT = 80

#
# hostconfig
#
HOST_CONFIG_FILE = "/etc/paradrop/paradrop_host_config.yaml"
DEFAULT_HOST_CONFIG_FILE = "~/.paradrop/hostconfig.default.yaml"
HOST_DATA_PARTITION = "/"

#
# Chute data directory is used to provide persistence for chute data.
# The developer can store files here and they will persist across chute
# updates and restarts (but not uninstallation).
#
# Note: we do not want this in SNAP_DATA because that path
# contains the snap version.  We want this path to stay constant across
# paradrop upgrades because chutes will have volumes mounted here.
#
# Internal is inside the chute; external is in the host.
#
INTERNAL_DATA_DIR = "/data/"
EXTERNAL_DATA_DIR = "~/.paradrop/{chute}/"

#
# System directory is used to share system information from the host
# down to the chute such as a list of devices connected to WiFi.  This
# is mounted read-only inside the chute.
#
# Internal is inside the chute; external is in the host.
#
INTERNAL_SYSTEM_DIR = "/paradrop/"
EXTERNAL_SYSTEM_DIR = "/var/run/paradrop/system/{chute}/"

#
# Username and password to access the private registry.
#
# TODO: The router should receive credentials from pdserver or use something
# unique like its API key.
#
REGISTRY_USERNAME = "routers"
REGISTRY_PASSWORD = "zai7geigh0ujahQu"

# Reject by default chute updates that would install an older version.  This
# has been set to False to fulfill the requirement that users be able to
# downgrade chutes.
REJECT_DOWNGRADE = False

DOCKER_BIN_DIR = "/usr/bin"

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

def loadSettings(mode="local", slist=[]):
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
    snapCommonPath = os.environ.get("SNAP_COMMON", None)

    if mode == "local":
        mod.HOME_DIR = os.path.join(os.path.expanduser("~"), ".paradrop/")
        mod.FC_CHUTESTORAGE_FILE = os.path.join(mod.HOME_DIR, "chutes")
        mod.EXTERNAL_DATA_DIR = os.path.join(mod.HOME_DIR, "{chute}/")
        mod.LOG_DIR = os.path.join(mod.HOME_DIR, "logs/")
        mod.KEY_DIR = os.path.join(mod.HOME_DIR, "keys/")
        mod.MISC_DIR = os.path.join(mod.HOME_DIR, "misc/")
        mod.CONFIG_FILE = os.path.join(mod.HOME_DIR, "config")
        mod.UCI_CONFIG_DIR = "/tmp/config.d"
        mod.UCI_BACKUP_DIR = "/tmp/config-backup.d"
        mod.HOST_CONFIG_FILE = "/tmp/hostconfig.yaml"
        mod.DEFAULT_HOST_CONFIG_FILE = "/tmp/hostconfig.default.yaml"

        mod.PDCONFD_WRITE_DIR = "/tmp/pdconfd"
        mod.HOST_DATA_PARTITION = mod.HOME_DIR

    elif mode == "unittest":
        mod.HOME_DIR = "/tmp/.paradrop-test/"
        mod.FC_CHUTESTORAGE_FILE = os.path.join(mod.HOME_DIR, "chutes")
        mod.EXTERNAL_DATA_DIR = os.path.join(mod.HOME_DIR, "{chute}/")
        mod.LOG_DIR = os.path.join(mod.HOME_DIR, "logs/")
        mod.KEY_DIR = os.path.join(mod.HOME_DIR, "keys/")
        mod.MISC_DIR = os.path.join(mod.HOME_DIR, "misc/")
        mod.CONFIG_FILE = os.path.join(mod.HOME_DIR, "config")
        mod.UCI_CONFIG_DIR = os.path.join(mod.HOME_DIR, "config.d")
        mod.UCI_BACKUP_DIR = os.path.join(mod.HOME_DIR, "config-backup.d")
        mod.HOST_CONFIG_FILE = os.path.join(mod.HOME_DIR, "hostconfig.yaml")
        mod.DEFAULT_HOST_CONFIG_FILE = os.path.join(mod.HOME_DIR, "hostconfig.default.yaml")

    elif snapCommonPath is not None:
        mod.FC_CHUTESTORAGE_FILE = os.path.join(snapCommonPath, "chutes")
        mod.EXTERNAL_DATA_DIR = os.path.join(snapCommonPath, "{chute}/")
        mod.LOG_DIR = os.path.join(snapCommonPath, "logs/")
        mod.KEY_DIR = os.path.join(snapCommonPath, "keys/")
        mod.MISC_DIR = os.path.join(snapCommonPath, "misc/")
        mod.CONFIG_FILE = os.path.join(snapCommonPath, "config")
        mod.UCI_CONFIG_DIR = os.path.join(snapCommonPath, "config.d")
        mod.UCI_BACKUP_DIR = os.path.join(snapCommonPath, "config-backup.d")
        mod.HOST_CONFIG_FILE = os.path.join(snapCommonPath, "hostconfig.yaml")
        mod.DEFAULT_HOST_CONFIG_FILE = os.path.join(snapCommonPath, "hostconfig.default.yaml")
        mod.HOST_DATA_PARTITION = "/writable"

        mod.DOCKER_BIN_DIR = "/snap/bin"

    for x in [mod.LOG_DIR, mod.KEY_DIR, mod.MISC_DIR]:
        if not os.path.exists(x):
            os.makedirs(x)

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
