
from paradrop.lib.utils.output import out, logPrefix

"""
    configservice module:
        This module is responsible for "poking" the proper host OS services
        to change the host OS config. This would include things like changing
        the networking, DHCP server settings, wifi, etc..
"""


def reloadNetwork(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
