###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from pdtools.lib.output import out
from paradrop.backend.exc import plangraph

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

#   # Check if the chute is new
#   # if(not old):
#   # convert cpu cgroups and add to lxcconfig (cached, key: 'cpuConfig')
#   chutePlan.addPlans(new, plangraph.RESOURCE_GET_VIRT_CPU, (new.getCpuConfigString, None))
#   
#   # convert mem cgroups and add to lxcconfig (cached, key: 'memConfig')
#   chutePlan.addPlans(new, plangraph.RESOURCE_GET_VIRT_MEM, (new.getMemConfigString, None))

#   # Generate a config file for wshaper, put in cache (key: 'osResourceConfig')
#   chutePlan.addPlans(new, plangraph.RESOURCE_GET_OS_CONFIG, (new.getOSResourceConfig, None))

#   # Make calls to configure the wshaper UCI file
#   todoPlan = (new.setOSResourceConfig, old)
#   abtPlan = (new.resetOSResourceConfig, None) 
#   chutePlan.addPlans(new, plangraph.RESOURCE_SET_VIRT_QOS, todoPlan, abtPlan)
#   
#   # Once all changes are made into UCI system, reload the wshaper daemon
#   todoPlan = (osenv.reloadQos, (chuteStor, new, True)) 
#   abtPlan = [(new.resetOSResourceConfig, None), (osenv.reloadQos, (chuteStor, new, False))]
#   chutePlan.addPlans(new, plangraph.RESOURCE_RELOAD_QOS, todoPlan, abtPlan)

    return None
