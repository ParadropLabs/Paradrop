###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################
import sys, os, hashlib, urllib2, tarfile

from lib.paradrop import *
from lib.paradrop.utils import pdutils
from lib.paradrop.chute import Chute
from lib.paradrop import chute
from lib.internal.utils import lxc as virt
from lib.internal.utils import openwrt as osenv
from lib.internal.utils import pdos
from lib.internal.utils import stats
from lib.internal.utils import security
from lib.internal.exc import plangraph
from lib.internal.fc import chutemanager
from lib.internal.fc.fcerror import PDFCError
from lib.internal.fc import macromanager

#
# Function called by the execution planner
#
def generateFilesPlan(chuteStor, newChute, chutePlan):
    
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
    out.header("-- %s Generating Files Plan: %r\n" % (logPrefix(), new))
    
    tok = new.getCache('updateToken')
    if(tok and tok == 'STARTINGUP'):
        starting = True
    else:
        starting = False

    # The Chute uses libraries borrowed from the host, copy them
    if(not old or starting):
        chutePlan.addPlans(new, plangraph.FILES_COPY_FROM_OS, (new.copyEssentials, None))

    # There are a few files (lxc_start.sh) that need to be copied from the /root/cXXXX/ dir into the mounted partition
    if(not old or starting):
        chutePlan.addPlans(new, plangraph.FILES_COPY_TO_MNT, (new.copyFilesToMount, None)) 
    
    # See if there is a change between the old.files and new.files
    if(old and old.files == new.files and not starting):
        return None

    # Are there any files?
    if(len(new.files) == 0):
        return None
    
    # Otherwise, we have files to download, so check for proper format first
    chutePlan.addPlans(new, plangraph.FILES_SECURITY_CHECK, (security.checkFiles, new))
    
    # Add plan to fetch the files
    chutePlan.addPlans(new, plangraph.FILES_FETCH, (new.fetchFiles, None))
    # Add plan to fetch the files
    chutePlan.addPlans(new, plangraph.FILES_COPY_USER, (new.copyFiles, None))
     

    ##################
    # This part is semi-complicated
    # If a chute was running/frozen and then some files in the chute are updated, we need to restart the chute as the new binaries/files won't be currently used.
    # This function will call the necessary lxc-start/stop commands
    # NOTE: we only need to do this when an old chute exists and the state is running/frozen.
    # Otherwise, the next lxc-start command will properly load the new binaries/data.
    # If fetchFiles does not make any changes, it will skip this function 

    if (old and (new.state == chute.STATE_RUNNING or new.state == chute.STATE_FROZEN)):
        currChuteState = stats.getLxcState(new.getInternalName()) 
        # We only want to reload when the chute is actually running
        # Could be power cycled and chutes would be stopped
        # In that case exc/state.py will handle that possibility, and start the chute
        if (currChuteState == chute.STATE_RUNNING or currChuteState == chute.STATE_FROZEN):
            chutePlan.addPlans(new, plangraph.STATE_FILES_STOP, (virt.fileStop, new))
            chutePlan.addPlans(new, plangraph.STATE_FILES_START, (virt.fileStart, new))


    return None

