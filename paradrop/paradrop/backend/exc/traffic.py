###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.backend.exc import plangraph
from paradrop.lib import config
from paradrop.lib.utils.output import out, logPrefix

def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.header("== %s %r\n" % (logPrefix(), update))
    
    # Make sure we need to create this chute (does it already exist)
    # TODO

    
    # First time, so generate the basic firewall rules in cache (key: 'osFirewallConfig')
    update.plans.addPlans(plangraph.TRAFFIC_GET_OS_FIREWALL, (config.firewall.getOSFirewallRules, ))
            
    # Combine rules from above two fucntions, save to file
    todoPlan = (config.firewall.setOSFirewallRules, )
    abtPlan = (config.osconfig.revertConfig, "firewall")
    update.plans.addPlans(plangraph.TRAFFIC_SET_OS_FIREWALL, todoPlan, abtPlan)
    
    # Reload firewall based on rule changes
    todoPlan = (config.configservice.reloadFirewall, )
    # To abort we first have to revert changes we made
    abtPlan = [(config.osconfig.revertConfig, "firewall"), (config.configservice.reloadFirewall, )]
    update.plans.addPlans(plangraph.TRAFFIC_RELOAD_FIREWALL, todoPlan, abtPlan)
    
    return None

###########################################################################################################
## Integrate from below
# import sys
# 
# from lib.paradrop import *
# from lib.paradrop.utils import pdutils
# from lib.paradrop.chute import Chute
# from lib.paradrop import chute
# 
# from lib.internal.utils import uci
# from lib.internal.utils import security
# from lib.internal.utils import openwrt as osenv
# from lib.internal.exc import plangraph
# from lib.internal.fc.fcerror import PDFCError
# from lib.internal.fc.chutestorage import ChuteStorage

#
# Function called by the execution planner
#
def generateTrafficPlan(chuteStor, newChute, chutePlan):
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
    out.header("-- %s Generating Traffic Plan: %r\n" % (logPrefix(), new))
    
    # First see if we are making new rules or changing old ones
    
    chutePlan.addPlans(new, plangraph.TRAFFIC_SECURITY_CHECK, (security.checkTraffic, (chuteStor, new)))
    
    # First time, so generate the basic firewall rules in cache (key: 'osFirewallConfig')
    chutePlan.addPlans(new, plangraph.TRAFFIC_GET_OS_FIREWALL, (new.getOSFirewallRules, chuteStor))

    # Generate developer rules to 'developerFirewallConfig' cache 
    chutePlan.addPlans(new, plangraph.TRAFFIC_GET_DEVELOPER_FIREWALL, (new.getDeveloperFirewallRules, None)) 
            
    # Combine rules from above two fucntions, save to file
    todoPlan = (new.setFirewallConfig, old)
    abtPlan = (new.resetOSFirewallConfig, None)
    chutePlan.addPlans(new, plangraph.TRAFFIC_SET_OS_FIREWALL, todoPlan, abtPlan)
    
    # Reload firewall based on rule changes
    todoPlan = (osenv.reloadFirewall, (chuteStor, new, False))
    # To abort we first have to revert changes we made
    abtPlan = [(new.resetOSFirewallConfig, None), (osenv.reloadFirewall, (chuteStor, new, True))]
    chutePlan.addPlans(new, plangraph.TRAFFIC_RELOAD_FIREWALL, todoPlan, abtPlan)
    
    return None

