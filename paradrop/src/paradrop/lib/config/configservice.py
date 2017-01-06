"""
    configservice module:
        This module is responsible for "poking" the proper host OS services
        to change the host OS config. This would include things like changing
        the networking, DHCP server settings, wifi, etc..
"""

import json

from paradrop.confd import client
from paradrop.lib.utils import uci
from paradrop.base.output import out


def reloadAll(update):
    # Note: reloading all config files at once seems safer than individual
    # files because of cross-dependencies.
    statusString = client.reloadAll()

    # Check the status to make sure all configuration sections
    # related to this chute were successfully loaded.
    #
    # We should only abort if there were problems related to this chute.
    # Example: a WiFi card was removed, so we fail to bring up old WiFi
    # interfaces; however, installing a new chute that does not depend on WiFi
    # should still succeed.
    status = json.loads(statusString)
    for section in status:
        if section['success']:
            continue

        if section['comment'] == update.new.name:
            raise Exception("Error preparing host environment for chute")
        else:
            out.warn("Error installing configuration section {} {} for chute {}".format(
                    section['type'], section['name'], section['comment']))
