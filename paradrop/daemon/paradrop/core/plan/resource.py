###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.base.output import out
from paradrop.core.config import resource
from paradrop.core.container import dockerapi
from . import plangraph

def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))

    update.plans.addPlans(plangraph.RESOURCE_GET_ALLOCATION,
            (resource.getResourceAllocation,))

    update.plans.addPlans(plangraph.RESOURCE_SET_ALLOCATION,
            (dockerapi.setResourceAllocation,),
            (dockerapi.revertResourceAllocation,))

    return None
