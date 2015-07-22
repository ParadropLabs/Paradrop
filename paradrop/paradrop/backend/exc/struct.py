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
    update.plans.addPlans(plangraph.STRUCT_GET_SYSTEM_DEVICES, (config.devices.getSystemDevices, ))
    update.plans.addPlans(plangraph.STRUCT_SET_SYSTEM_DEVICES, (config.devices.setSystemDevices, ))
    
    # Save current network configuration into chute cache (key: 'networkInterfaces')
    update.plans.addPlans(plangraph.STRUCT_GET_INT_NETWORK, (config.network.getNetworkConfig, ))

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

    # Now deal with reloading the network
    todoPlan = (config.configservice.reloadNetwork, )
    # If we need to abort, we first need to undo the OS Network config changes we made, so the abort plan is a list here
    abtPlan = [(config.osconfig.revertConfig, 'wireless'),
                (config.osconfig.revertConfig, 'network'),
                (config.configservice.reloadNetwork, )]
    
    update.plans.addPlans(plangraph.STRUCT_RELOAD_NETWORK, todoPlan, abtPlan)
    
    # Now deal with reloading wifi, NOTE that reloadNetwork does a wifi call too, so we only expect wifi to be
    # called in cases when network was NOT called, this is required to deal with issues of when the developer changes
    # wifi settings only (like SSID) but no network settings
    todoPlan = (config.configservice.reloadWireless, )
    # If we need to abort, we first need to undo the OS Wireless config changes we made, so the abort plan is a list here
    abtPlan = [(config.osconfig.revertConfig, 'wireless'), (config.configservice.reloadWireless, )]
    update.plans.addPlans(plangraph.STRUCT_RELOAD_WIFI, todoPlan, abtPlan)

    return None

