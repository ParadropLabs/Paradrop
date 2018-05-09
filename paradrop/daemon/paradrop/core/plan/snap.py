###################################################################
# Copyright 2013-2016 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
This module generates update plans for a snap operation.
"""

from paradrop.base.output import out
from paradrop.core.config import snap
from . import plangraph


def generatePlans(update):
    out.verbose("%r\n" % (update))

    update.plans.addPlans(plangraph.SNAP_INSTALL,
                          (snap.updateSnap, ))
