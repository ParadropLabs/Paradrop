###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.backend.exc import plangraph
from paradrop.lib import config
from pdtools.lib.output import out

def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.header("%r\n" % (update))
    
    # Make sure we need to create this chute (does it already exist)
    # TODO
#    chutePlan.addPlans(new, plangraph.TRAFFIC_SECURITY_CHECK, (security.checkTraffic, (chuteStor, new)))
   
    # First time, so generate the basic firewall rules in cache (key: 'osFirewallConfig')
    update.plans.addPlans(plangraph.TRAFFIC_GET_OS_FIREWALL, (config.firewall.getOSFirewallRules, ))

    # Get developer firewall rules (key: 'developerFirewallRules')
    update.plans.addPlans(plangraph.TRAFFIC_GET_DEVELOPER_FIREWALL, (config.firewall.getDeveloperFirewallRules, ))
            
    # Combine rules from above two fucntions, save to file
    todoPlan = (config.firewall.setOSFirewallRules, )
    abtPlan = (config.osconfig.revertConfig, "firewall")
    update.plans.addPlans(plangraph.TRAFFIC_SET_OS_FIREWALL, todoPlan, abtPlan)
    
    return None
