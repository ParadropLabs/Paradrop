###################################################################
# Copyright 2013-2016 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
This module generates update plans for a snap operation.
"""

from paradrop.base.output import out
from paradrop.lib.config import snap
from . import plangraph


def generatePlans(update):
    out.verbose("%r\n" % (update))

    # Check if requested version is already installed.
    update.plans.addPlans(plangraph.SNAP_CHECK_VERSION,
                          (snap.checkVersion, ))

    # Begin installation of the snap - makes a call to pdinstall.
    update.plans.addPlans(plangraph.SNAP_INSTALL,
                          (snap.beginInstall, ))
