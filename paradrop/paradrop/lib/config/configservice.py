"""
    configservice module:
        This module is responsible for "poking" the proper host OS services
        to change the host OS config. This would include things like changing
        the networking, DHCP server settings, wifi, etc..
"""

from paradrop.lib.utils.output import out, logPrefix


def reloadNetwork(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.

def reloadWireless(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.

def reloadFirewall(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.

def reloadQos(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.

def reloadDHCP(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # leverage osconfig to poke pdconfd to tell it we have made changes
    # to the file specified.
