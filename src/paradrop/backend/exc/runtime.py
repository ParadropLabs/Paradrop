###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################
import sys

from lib.paradrop import *
from lib.paradrop.chute import Chute
from lib.paradrop import chute

from lib.internal.exc import plangraph
from lib.internal.fc.fcerror import PDFCError
from lib.internal.fc.chutestorage import ChuteStorage
from lib.internal.utils import lxc as virt
from lib.internal.utils import security

#
# Function called by the execution planner
#
def generateRuntimePlan(chuteStor, newChute, chutePlan):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute, then adds Plan() calls
        to make the Chute match the @newChute.

        Returns:
            None  : means continue to pass this chute update to the rest of the chain.
            True  : means stop updating, but its ok (no errors or anything)
            str   : means stop updating, but some error occured (contained in the string)
    """
    new = newChute
    old = chuteStor.getChute(newChute.guid)
    out.header("-- %s Generating Runtime Plan: %r\n" % (logPrefix(), new))

    # Always need to check security
    chutePlan.addPlans(new, plangraph.RUNTIME_SECURITY_CHECK, (security.checkRuntime, (chuteStor, new)))

    # Generate virt start script, stored in cache (key: 'virtScript')
    chutePlan.addPlans(new, plangraph.RUNTIME_GET_VIRT_SCRIPT, (new.getVirtScript, None))
    
    # If the user specifies DHCP then we need to generate the config and store it to disk
    chutePlan.addPlans(new, plangraph.RUNTIME_GET_VIRT_DHCP, (new.getVirtDHCPSettings, None))
    chutePlan.addPlans(new, plangraph.RUNTIME_SET_VIRT_DHCP, (new.setVirtDHCPSettings, None))

    return None

