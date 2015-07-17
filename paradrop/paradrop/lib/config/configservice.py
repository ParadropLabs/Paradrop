"""
    configservice module:
        This module is responsible for "poking" the proper host OS services
        to change the host OS config. This would include things like changing
        the networking, DHCP server settings, wifi, etc..
"""

from paradrop.backend.pdconfd import client
from paradrop.lib.utils import uci
from pdtools.lib.output import out

def reloadNetwork(update):
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.
    client.reload(uci.getSystemPath("network"))

def reloadWireless(update):
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.
    client.reload(uci.getSystemPath("wireless"))

def reloadFirewall(update):
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.
    client.reload(uci.getSystemPath("firewall"))

def reloadQos(update):
    out.warn('TODO implement me\n' )
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.

def reloadDHCP(update):
    out.warn('TODO implement me\n' )
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.
