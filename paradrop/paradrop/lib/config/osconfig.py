"""
    osconfig module:
        This module is in charge of changing configuration files for
        pdfcd on the host OS. This relates to things like network, dhcp,
        wifi, firewall changes. Pdfcd should be able to make simple abstracted
        calls into this module so that if we need to change what type of OS config
        we need to support only this module would change.
"""

from paradrop.lib.config.uciutils import restoreConfigFile
from pdtools.lib.output import out


def revertConfig(update, theType):
    """
    Basically the UCI system saves a backup of the original config file, if
    we need to revert changes at all, we can just tell our UCI module to
    revert back using that backup copy.
    """
    restoreConfigFile(update.new, theType)
