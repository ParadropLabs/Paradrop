"""
    configservice module:
        This module is responsible for "poking" the proper host OS services
        to change the host OS config. This would include things like changing
        the networking, DHCP server settings, wifi, etc..
"""
import json

from paradrop.backend.pdconfd import client
from paradrop.lib.utils import uci
from pdtools.lib.output import out


def reloadAll(update):
    # Note: reloading all config files at once seems safer than individual
    # files because of cross-dependencies.
    statusString = client.reloadAll()

    # Check the status to make sure all configuration sections
    # related to this chute were successfully loaded.
    status = json.loads(statusString)
    for section in status:
        if section['comment'] == update.name:
            if not section['success']:
                out.err("Error installing configuration section {} {}".format(
                        section['type'], section['name']))
                raise Exception("Error preparing host environment for chute")
