
from paradrop.lib.utils.output import out, logPrefix


"""
    osconfig module:
        This module is in charge of changing configuration files for
        pdfcd on the host OS. This relates to things like network, dhcp,
        wifi, firewall changes. Pdfcd should be able to make simple abstracted
        calls into this module so that if we need to change what type of OS config
        we need to support only this module would change.
"""
