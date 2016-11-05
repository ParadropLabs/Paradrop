###################################################################
# Copyright 2013-2016 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
This module generates update plans for a snap operation.
"""

from paradrop.base.lib.output import out
from paradrop.backend.exc import plangraph
from paradrop.lib import config

def generatePlans(update):
    out.verbose("%r\n" % (update))

    # Check if requested version is already installed.
    update.plans.addPlans(plangraph.SNAP_CHECK_VERSION,
                          (config.snap.checkVersion, ))

    # Begin installation of the snap - makes a call to pdinstall.
    update.plans.addPlans(plangraph.SNAP_INSTALL,
                          (config.snap.beginInstall, ))
