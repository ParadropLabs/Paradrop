###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import sys

from lib.paradrop import *
from lib.paradrop.chute import Chute
from lib.paradrop import chute

from lib.internal.utils import uci
from lib.internal.utils import security
from lib.internal.fc import networkmanager
from lib.internal.utils import lxc as virt
from lib.internal.utils import coap
from lib.internal.utils import openwrt as osenv
from lib.internal.exc import plangraph
from lib.internal.fc.fcerror import PDFCError
from lib.internal.fc.chutestorage import ChuteStorage

#
# Function called by the execution planner
#
def generateStructPlan(chuteStor, clickHandler, ofHandler, newChute, chutePlan):
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
    out.header("-- %s Generating Struct Plan: %r\n" % (logPrefix(), new))
    #print("New chute: %s" % new.dumpCache())
    #print("Old chute: %s" % old.dumpCache())
                
    # First need to check security of the stuff they have changed
    # chutePlan.addPlans(new, plangraph.STRUCT_SECURITY_CHECK, (security.checkStruct, (chuteStor, new)))  

    # Save current network configuration into chute cache (key: 'networkInterfaces')
    chutePlan.addPlans(new, plangraph.STRUCT_GET_INT_NETWORK, (new.getNetworkConfig, chuteStor))

    # Setup changes to push into OS config files (key: 'osNetworkConfig')
    chutePlan.addPlans(new, plangraph.STRUCT_GET_OS_NETWORK, (new.getOSNetworkConfig, None))  
    
    # Setup changes to push into OS config files (key: 'osWirelessConfig')
    chutePlan.addPlans(new, plangraph.STRUCT_GET_OS_WIRELESS, (new.getOSWirelessConfig, None))  
    
    # Setup changes into virt configuration file (key: 'virtNetworkConfig')
    chutePlan.addPlans(new, plangraph.STRUCT_GET_VIRT_NETWORK, (new.getVirtNetworkConfig, None))
    
    # Push changes into OS config files
    todoPlan = (new.setOSNetworkConfig, old)
    abtPlan = (new.resetOSNetworkConfig, None)
    chutePlan.addPlans(new, plangraph.STRUCT_SET_OS_NETWORK, todoPlan, abtPlan)
    
    todoPlan = (new.setOSWirelessConfig, old)
    abtPlan = (new.resetOSWirelessConfig, None)
    chutePlan.addPlans(new, plangraph.STRUCT_SET_OS_WIRELESS, todoPlan, abtPlan)

    # Now deal with reloading the network
    todoPlan = (osenv.reloadNetwork, (clickHandler, ofHandler, chuteStor, new, False))
    # If we need to abort, we first need to undo the OS Network config changes we made, so the abort plan is a list here
    abtPlan = [(new.resetOSWirelessConfig, None), (new.resetOSNetworkConfig, None), (osenv.reloadNetwork, (clickHandler, ofHandler, chuteStor, new, True))]
    chutePlan.addPlans(new, plangraph.STRUCT_RELOAD_NETWORK, todoPlan, abtPlan)
   
    if (new.apptype == 'virtnet'):
        # If the user specifies DHCP then we need to generate the config and store it to disk
        chutePlan.addPlans(new, plangraph.DHCP_GET_VIRT_RULES, (new.getDHCPConfig, chuteStor))

        chutePlan.addPlans(new, plangraph.DHCP_SET_VIRT_RULES, (new.setDHCPConfig, old))


        # Once all changes are made into UCI system, reload the wshaper daemon
        todoPlan = (osenv.reloadDHCP, (chuteStor, new, False)) 
        abtPlan = [(new.resetDHCPConfig, None), (osenv.reloadDHCP, (chuteStor, new, True))]
        chutePlan.addPlans(new, plangraph.DHCP_RELOAD, todoPlan, abtPlan)

    # Now deal with reloading wifi, NOTE that reloadNetwork does a wifi call too, so we only expect wifi to be
    # called in cases when network was NOT called, this is required to deal with issues of when the developer changes
    # wifi settings only (like SSID) but no network settings
    todoPlan = (osenv.reloadWireless, (clickHandler, chuteStor, new, True))
    # If we need to abort, we first need to undo the OS Wireless config changes we made, so the abort plan is a list here
    abtPlan = [(new.resetOSWirelessConfig, None), (osenv.reloadWireless, (clickHandler, chuteStor, new, False))]
    chutePlan.addPlans(new, plangraph.STRUCT_RELOAD_WIFI, todoPlan, abtPlan)

    chutePlan.addPlans(new, plangraph.COAP_CHANGE_PROCESSES, (coap.startNewClickProcess, (new, chuteStor, clickHandler)))
    return None
