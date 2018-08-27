"""
    configservice module:
        This module is responsible for "poking" the proper host OS services
        to change the host OS config. This would include things like changing
        the networking, DHCP server settings, wifi, etc..
"""

import json

from paradrop.confd import client
from paradrop.base.output import out


def reload_placeholder(update):
    """
    This function successfully does nothing.

    It serves as a placeholder so that we can attach an abort function to a
    specific point in the update pipeline.
    """
    pass


def reloadAll(update):
    """
    Reload pdconf configuration files.
    """
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
        # Checking age > 0 filters out errors that occurred in the past.
        if section['success'] or section['age'] > 0:
            continue

        message = "Error installing configuration section {} {} for chute {}".format(
                section['type'], section['name'], section['comment'])
        if section['comment'] == update.new.name:
            raise Exception(message)
        else:
            out.warn(message)
