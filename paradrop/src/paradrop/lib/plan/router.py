###################################################################
# Copyright 2013-2016 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
This module generates update plans for router operations such as factory reset.
"""

from paradrop.base.output import out
from paradrop.lib.config import state
from paradrop.lib.container import dockerapi

from . import plangraph


def generatePlans(update):
    out.verbose("%r\n" % (update))

    if update.updateType == "factoryreset":
        update.plans.addPlans(plangraph.STATE_CALL_STOP,
                              (dockerapi.removeAllContainers, ))

        update.plans.addPlans(plangraph.STATE_SAVE_CHUTE,
                              (state.saveChute, ))
