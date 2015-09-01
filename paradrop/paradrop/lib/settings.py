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

    These settings can be overriden by a file defined which contains the following syntax:

        # This changes a string default setting
        EXACT_SETTING_NAME0 "new string setting"
        
        # This changes a int default setting
        EXACT_SETTING_NAME1 int0

    If settings need to be changed, they should be done so by the initialization code
    (such as pdfcd, pdapi_server, pdfc_config, etc...)

    This is done by calling the following function:
        settings.updateSettings(filepath)
"""

import os
import re
import sys

DEBUG_MODE = False
# VERBOSE = False

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

FC_CHUTESTORAGE_SAVE_PATH = "chutes"
FC_CHUTESTORAGE_SAVE_TIMER = 60
RESERVED_CHUTE = "__PARADROP__"

#
# Host configuration file
#
HOST_CONFIG_PATH = "/etc/paradrop_host_config"

#
# UCI configuration files
#
UCI_CONFIG_DIR = "/etc/config"

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

    # Adjust default paths if we are running under Snappy
    dataPath = os.environ.get("SNAP_APP_DATA_PATH", None)
    if dataPath is not None:
        mod.FC_CHUTESTORAGE_SAVE_PATH = os.path.join(dataPath, "chutes")
        mod.UCI_CONFIG_DIR = os.path.join(dataPath, "config.d")
        mod.HOST_CONFIG_PATH = os.path.join(dataPath, "hostconfig.yaml")

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
