###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.base.output import out
from paradrop.core.config import dockerconfig, osconfig, configservice, dhcp
from . import plangraph


def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))

    # Generate virt start script, stored in cache (key: 'virtPreamble')
    update.plans.addPlans(plangraph.RUNTIME_GET_VIRT_PREAMBLE, (dockerconfig.getVirtPreamble, ))

    # Make sure volume directories exist.
    update.plans.addPlans(plangraph.CREATE_VOLUME_DIRS,
            (dockerconfig.createVolumeDirs, ),
            (dockerconfig.abortCreateVolumeDirs, ))

    # If the user specifies DHCP then we need to generate the config and store it to disk
    update.plans.addPlans(plangraph.RUNTIME_GET_VIRT_DHCP, (dhcp.getVirtDHCPSettings, ))
    update.plans.addPlans(plangraph.RUNTIME_SET_VIRT_DHCP, (dhcp.setVirtDHCPSettings, ))

    # Reload configuration files
    todoPlan = (configservice.reloadAll, )
    abtPlan = [(osconfig.revertConfig, "dhcp"),
               (osconfig.revertConfig, "firewall"),
               (osconfig.revertConfig, "network"),
               (osconfig.revertConfig, "wireless"),
               (configservice.reloadAll, )]
    update.plans.addPlans(plangraph.RUNTIME_RELOAD_CONFIG, todoPlan, abtPlan)

    return None
