###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.base.output import out
from paradrop.core.config import security

from . import plangraph


def generatePlans(update):
    """
    This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
    then adds Plan() calls to make the Chute match the @newChute.

    Returns:
        True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))

    update.plans.addPlans(plangraph.ENFORCE_ACCESS_RIGHTS,
                          (security.enforce_access_rights, ))

    return None
