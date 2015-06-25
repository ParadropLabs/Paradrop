###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import sys, os

from lib.paradrop import *
from lib.paradrop.chute import Chute
from lib.paradrop import chute
from lib.paradrop.utils import pdutils as pdutil

from lib.internal.exc import plangraph
from lib.internal.fc import chutemanager
from lib.internal.utils import lxc as virt
from lib.internal.utils import pdos
from lib.internal.utils import stats
from lib.internal.utils import openwrt as osenv
from lib.internal.fc.fcerror import PDFCError

#
# Function called by the execution planner
#
def generateStatePlan(chuteStor, newChute, chutePlan):
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
    out.header("-- %s Generating State Plan: %r\n" % (logPrefix(), new))
   
    # Was there an old chute?
    if(not old):
        out.verbose('-- %s brand new chute\n' % logPrefix())
        
        # If we are now running then everything has to be setup for the first time
        if(new.state == chute.STATE_RUNNING):
            chutePlan.addPlans(new, plangraph.STATE_CALL_START, (virt.startChute, new))
        
        # Check if the state is invalid, we should return bad things in this case (don't do anything)
        elif(new.state == chute.STATE_INVALID):
            return True
        
        # Call this function to make sure the lxc_start script is executable
        s0 = chutemanager.getMntVirtScriptPath(new)
        chutePlan.addPlans(new, plangraph.STATE_MAKE_EXEC, (pdos.makeExecutable, s0))
        
        # The create command generates an internal config file, save it for later
        chutePlan.addPlans(new, plangraph.STATE_SAVE_CFG, (virt.saveChuteConfig, new))
        
        # If there wasn't a old one we need to configure this one
        chutePlan.addPlans(new, plangraph.STATE_CALL_CFG, (virt.configureChute, new))

    # There is an old Chute, see if the state changed
    else:
        if(new.state != old.state):
            if(pdutil.isValidStateTransition(old.state, new.state)):
                out.info('-- %s State change required: %s -> %s\n' % (logPrefix(), old.state, new.state))
                os = old.state
                ns = new.state
                # We already verified its a valid state change, so less to check here
                if(ns == chute.STATE_FROZEN):
                    chutePlan.addPlans(new, plangraph.STATE_CALL_FREEZE, (virt.freezeChute, new))
                elif(ns == chute.STATE_RUNNING and os == chute.STATE_FROZEN):
                    chutePlan.addPlans(new, plangraph.STATE_CALL_UNFREEZE, (virt.unfreezeChute, new))
                elif(ns == chute.STATE_RUNNING):
                    chutePlan.addPlans(new, plangraph.STATE_CALL_START, (virt.startChute, new))
                elif(ns == chute.STATE_STOPPED):
                    chutePlan.addPlans(new, plangraph.STATE_CALL_STOP, (virt.stopChute, new))
                # TODO - test if needs to be moved to specific transitions
                # Some transitions might need the             
                return False #Change state, but don't perform everything else

            else:
                out.warn('** %s Invalid state change discovered: %s -> %s\n' % (logPrefix(), old.state, new.state))
                return "Invalid state change, cannot go from %s -> %s\n" % (old.state, new.state)
        
        else: #New State is the same as old state, (could be a Startup)
            tok = new.getCache('updateToken')
            if (tok and tok == 'STARTINGUP'):
                # Call this function to make sure the lxc_start script is executable
                s0 = chutemanager.getMntVirtScriptPath(new)
                chutePlan.addPlans(new, plangraph.STATE_MAKE_EXEC, (pdos.makeExecutable, s0))
                #restore chute config by calling configureChute
                chutePlan.addPlans(new, plangraph.STATE_CALL_CFG, (virt.configureChute, new))
               
                currChuteState = stats.getLxcState(new.getInternalName()) 
                #Only want to change when AP was power cycled, not just when pdfcd restarts
                if (currChuteState == chute.STATE_STOPPED):
                    #if state was running, need to actually start the chute
                    if(new.state == chute.STATE_RUNNING):
                        chutePlan.addPlans(new, plangraph.STARTUP_CALL_EARLY_START, (virt.startChute, new))
                    elif(new.state == chute.STATE_FROZEN):
                        chutePlan.addPlans(new, plangraph.STARTUP_CALL_EARLY_START, (virt.startChute, new))
                        chutePlan.addPlans(new, plangraph.STATE_CALL_FREEZE, (virt.freezeChute, new))
    
    # The last plans we need to add are to write virt config and script to file (the set* commands)
    chutePlan.addPlans(new, plangraph.STATE_SET_VIRT_CONFIG, (virt.setVirtConfig, new), (virt.resetVirtConfig, new))
    chutePlan.addPlans(new, plangraph.STATE_SET_VIRT_SCRIPT, (virt.setVirtScript, new), (virt.resetVirtScript, new))

    # Everything is OK
    return None

