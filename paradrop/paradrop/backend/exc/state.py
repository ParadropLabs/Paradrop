###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.lib.utils.output import out, logPrefix
from paradrop.backend.exc import plangraph
from paradrop.lib import chute
from paradrop.lib.utils.pdutils import jsonPretty

from paradrop.lib.utils import dockerapi as virt

def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))
    
    # If this chute is new (no old version)
    if(update.old is None):
        out.verbose('new chute\n' )
        
        #If it's a stop  or start command go ahead and fail right now since we don't have a record of it
        if update.updateType == 'stop' or update.updateType == 'start':
            update.failure ="No chute found with id: " + update.name
            return True
        # If we are now running then everything has to be setup for the first time
        if(update.new.state == chute.STATE_RUNNING):
            update.plans.addPlans(plangraph.STATE_CALL_START, (virt.startChute,))
        
        # Check if the state is invalid, we should return bad things in this case (don't do anything)
        elif(update.new.state == chute.STATE_INVALID):
            if(settings.DEBUG_MODE):
                update.responses.append('Chute state is invalid')
            return True
    
    # Not a new chute
    else:
        if update.updateType == 'start':
            if update.old.state == chute.STATE_RUNNING :
                update.failure = update.name +" already running."
                return True
            update.plans.addPlans(plangraph.STATE_CALL_STOP, (virt.restartChute,))
        elif update.updateType == 'create':
            update.failure = update.name + " already exists on this device."
            return True
        elif update.new.state == chute.STATE_STOPPED :
            if update.updateType == 'delete':
                update.plans.addPlans(plangraph.STATE_CALL_STOP, (virt.removeChute,))
            if update.updateType == 'stop':
                if update.old.state == chute.STATE_STOPPED :
                    update.failure = update.name +" already stopped."
                    return True
                update.plans.addPlans(plangraph.STATE_CALL_STOP, (virt.stopChute,))
        pass

    return None

###########################################################################################################
## Integrate from below

# from lib.paradrop.chute import Chute
# from lib.paradrop import chute
# from lib.paradrop.utils import pdutils as pdutil
# from lib.internal.exc import plangraph
# from lib.internal.fc import chutemanager
# from lib.internal.utils import lxc as virt
# from lib.internal.utils import pdos
# from lib.internal.utils import stats
# from lib.internal.utils import openwrt as osenv
# from lib.internal.fc.fcerror import PDFCError


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
    out.header("Generating State Plan: %r\n" % (new))
   
    # Was there an old chute?
    if(not old):
        out.verbose('brand new chute\n' )
        
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
                out.info('State change required: %s -> %s\n' % (old.state, new.state))
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
                out.warn('Invalid state change discovered: %s -> %s\n' % (old.state, new.state))
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

