###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.base.output import out
from paradrop.core.config import devices, files, network, hostconfig, reservations, wifi

from . import plangraph


def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))

    update.plans.addPlans(plangraph.DOWNLOAD_CHUTE_FILES,
                          (files.download_chute_files, ),
                          (files.delete_chute_files, ))

    update.plans.addPlans(plangraph.LOAD_CHUTE_CONFIGURATION,
                          (files.load_chute_configuration, ))

    # Detect system devices and set up basic configuration for them (WAN
    # interface, wireless devices).  These steps do not need to be reverted on
    # abort.
    #
    # abortNetworkConfig is added as an abort command here so that it runs when
    # config.network.getNetworkConfig or just about anything else fails.
    update.plans.addPlans(plangraph.STRUCT_GET_SYSTEM_DEVICES,
                          (devices.getSystemDevices, ),
                          (network.abortNetworkConfig, ))

    update.plans.addPlans(plangraph.STRUCT_GET_RESERVATIONS,
                          (reservations.getReservations, ))

    update.plans.addPlans(plangraph.STRUCT_GET_HOST_CONFIG,
                          (hostconfig.getHostConfig, ))
    update.plans.addPlans(plangraph.STRUCT_SET_HOST_CONFIG,
                          (hostconfig.setHostConfig, ),
                          (hostconfig.revertHostConfig, ))

    # Save current network configuration into chute cache (key: 'networkInterfaces')
    update.plans.addPlans(plangraph.STRUCT_GET_INT_NETWORK,
                          (network.getNetworkConfig, ))

    # Setup changes to push into OS config files (key: 'osNetworkConfig')
    update.plans.addPlans(plangraph.STRUCT_GET_OS_NETWORK, (network.getOSNetworkConfig, ))

    # Setup changes to push into OS config files (key: 'osWirelessConfig')
    update.plans.addPlans(plangraph.STRUCT_GET_OS_WIRELESS, (wifi.getOSWirelessConfig, ))

    # Changes for networking
    todoPlan = (network.setOSNetworkConfig, )
    abtPlan = (network.revert_os_network_config, )
    update.plans.addPlans(plangraph.STRUCT_SET_OS_NETWORK, todoPlan, abtPlan)

    # Changes for wifi
    todoPlan = (wifi.setOSWirelessConfig, )
    abtPlan = (wifi.revert_os_wireless_config, )
    update.plans.addPlans(plangraph.STRUCT_SET_OS_WIRELESS, todoPlan, abtPlan)

    # Layer 3 bridging support
    todoPlan = (network.getL3BridgeConfig, )
    update.plans.addPlans(plangraph.STRUCT_GET_L3BRIDGE_CONFIG, todoPlan)

    todoPlan = (network.setL3BridgeConfig, )
    abtPlan = (network.revert_l3_bridge_config, )
    update.plans.addPlans(plangraph.STRUCT_SET_L3BRIDGE_CONFIG, todoPlan, abtPlan)

    return None
