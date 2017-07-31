###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.base.output import out
from paradrop.core.config import devices, network, hostconfig, osconfig, reservations, wifi

from . import plangraph


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

    # Setup changes into virt configuration file (key: 'virtNetworkConfig')
    update.plans.addPlans(plangraph.STRUCT_GET_VIRT_NETWORK, (network.getVirtNetworkConfig, ))

    # Changes for networking
    todoPlan = (network.setOSNetworkConfig, )
    abtPlan = (osconfig.revertConfig, 'network')
    update.plans.addPlans(plangraph.STRUCT_SET_OS_NETWORK, todoPlan, abtPlan)

    # Changes for wifi
    todoPlan = (wifi.setOSWirelessConfig, )
    abtPlan = (osconfig.revertConfig, 'wireless')
    update.plans.addPlans(plangraph.STRUCT_SET_OS_WIRELESS, todoPlan, abtPlan)

    return None
