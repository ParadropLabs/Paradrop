###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from pdtools.lib.output import out
from paradrop.backend.exc import plangraph

from paradrop.lib import config

def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))
    
    # Generate virt start script, stored in cache (key: 'virtPreamble')
    update.plans.addPlans(plangraph.RUNTIME_GET_VIRT_PREAMBLE, (config.dockerconfig.getVirtPreamble, ))
    
    # If the user specifies DHCP then we need to generate the config and store it to disk
    update.plans.addPlans(plangraph.RUNTIME_GET_VIRT_DHCP, (config.dhcp.getVirtDHCPSettings, ))
    update.plans.addPlans(plangraph.RUNTIME_SET_VIRT_DHCP, (config.dhcp.setVirtDHCPSettings, ))

    # Reload configuration files
    todoPlan = (config.configservice.reloadAll, )
    abtPlan = [(config.osconfig.revertConfig, "dhcp"),
               (config.osconfig.revertConfig, "firewall"),
               (config.osconfig.revertConfig, "network"),
               (config.osconfig.revertConfig, "wireless"),
               (config.configservice.reloadAll, )]
    update.plans.addPlans(plangraph.RUNTIME_RELOAD_CONFIG, todoPlan, abtPlan)

    return None
