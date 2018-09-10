###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.base.output import out
from paradrop.core.config import dockerconfig, configservice, dhcp
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

    todoPlan = (dhcp.setVirtDHCPSettings, )
    abtPlan = (dhcp.revert_dhcp_settings, )
    update.plans.addPlans(plangraph.RUNTIME_SET_VIRT_DHCP, todoPlan, abtPlan)

    # Reload configuration files
    todoPlan = (configservice.reloadAll, )
    update.plans.addPlans(plangraph.RUNTIME_RELOAD_CONFIG, todoPlan)

    # Reload configuration files if aborting.  This needs to happen at the
    # right place in the update pipeline such that UCI files have been
    # restored to their previous contents.
    todoPlan = (configservice.reload_placeholder, )
    abtPlan = (configservice.reloadAll, )
    update.plans.addPlans(plangraph.RUNTIME_RELOAD_CONFIG_BACKOUT, todoPlan, abtPlan)

    return None
