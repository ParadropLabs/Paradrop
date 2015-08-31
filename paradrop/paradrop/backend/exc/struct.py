###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from pdtools.lib.output import out
from paradrop.backend.exc import plangraph

from paradrop.lib import config

def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))

    # Detect system devices and set up basic configuration for them (WAN
    # interface, wireless devices).  These steps do not need to be reverted on
    # abort.
    #
    # abortNetworkConfig is added as an abort command here so that it runs when
    # config.network.getNetworkConfig or just about anything else fails.
    #
    # reloadAll is added as an abort command here so that it runs when any of
    # the set* plans fail and back out.
    update.plans.addPlans(plangraph.STRUCT_GET_SYSTEM_DEVICES,
                          (config.devices.getSystemDevices, ),
                          (config.network.abortNetworkConfig, ))
    update.plans.addPlans(plangraph.STRUCT_SET_SYSTEM_DEVICES,
                          (config.devices.setSystemDevices, ),
                          (config.configservice.reloadAll, ))

    update.plans.addPlans(plangraph.STRUCT_GET_HOST_CONFIG,
                          (config.hostconfig.getHostConfig, ))
    
    # Save current network configuration into chute cache (key: 'networkInterfaces')
    update.plans.addPlans(plangraph.STRUCT_GET_INT_NETWORK,
                          (config.network.getNetworkConfig, ))

    # Setup changes to push into OS config files (key: 'osNetworkConfig')
    update.plans.addPlans(plangraph.STRUCT_GET_OS_NETWORK, (config.network.getOSNetworkConfig, ))  
    
    # Setup changes to push into OS config files (key: 'osWirelessConfig')
    update.plans.addPlans(plangraph.STRUCT_GET_OS_WIRELESS, (config.wifi.getOSWirelessConfig, ))  
    
    # Setup changes into virt configuration file (key: 'virtNetworkConfig')
    update.plans.addPlans(plangraph.STRUCT_GET_VIRT_NETWORK, (config.network.getVirtNetworkConfig, ))
    
    # Changes for networking
    todoPlan = (config.network.setOSNetworkConfig, )
    abtPlan = (config.osconfig.revertConfig, 'network')
    update.plans.addPlans(plangraph.STRUCT_SET_OS_NETWORK, todoPlan, abtPlan)
    
    # Changes for wifi
    todoPlan = (config.wifi.setOSWirelessConfig, )
    abtPlan = (config.osconfig.revertConfig, 'wireless')
    update.plans.addPlans(plangraph.STRUCT_SET_OS_WIRELESS, todoPlan, abtPlan)

    return None
