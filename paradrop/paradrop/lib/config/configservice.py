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
    #client.reload(uci.getSystemPath("network"))
    pass

def reloadWireless(update):
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.
    #client.reload(uci.getSystemPath("wireless"))
    pass

def reloadFirewall(update):
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.
    #client.reload(uci.getSystemPath("firewall"))
    pass

def reloadQos(update):
    out.warn('TODO implement me\n' )
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.

def reloadDHCP(update):
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.
    #client.reload(uci.getSystemPath("dhcp"))
    pass

def reloadAll(update):
    # Note: reloading all config files at once seems safer than individual
    # files because of cross-dependencies.
    client.reloadAll()
