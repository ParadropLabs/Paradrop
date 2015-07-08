###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.lib.utils.output import out, logPrefix
from paradrop.backend.exc import plangraph

from paradrop.lib.config import dockerconfig as virtConfig

def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("   %s %r\n" % (logPrefix(), update))
    
    # Generate virt start script, stored in cache (key: 'virtPreamble')
    update.plans.addPlans(plangraph.RUNTIME_GET_VIRT_PREAMBLE, (virtConfig.getVirtPreamble, ))
    
    # If the user specifies DHCP then we need to generate the config and store it to disk
    update.plans.addPlans(plangraph.RUNTIME_GET_VIRT_DHCP, (virtConfig.getVirtDHCPSettings, ))
    update.plans.addPlans(plangraph.RUNTIME_SET_VIRT_DHCP, (virtConfig.setVirtDHCPSettings, ))

    return None

