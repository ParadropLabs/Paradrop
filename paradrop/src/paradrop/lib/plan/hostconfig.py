###################################################################
# Copyright 2013-2016 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
This module generates update plans for a host configuration operation.  It is
separate from the modules that generate plans for chute operations because we
only need to do a subset of the operations.
"""

from paradrop.base.output import out
from paradrop.lib.config import devices, network, configservice, hostconfig, osconfig

from . import plangraph


def generatePlans(update):
    out.verbose("%r\n" % (update))

    # Detect system devices and set up basic configuration for them (WAN
    # interface, wireless devices).  These steps do not need to be reverted on
    # abort.
    #
    # checkSystemDevices may reboot the machine if expected devices are
    # missing.
    #
    # abortNetworkConfig is added as an abort command here so that it runs when
    # config.network.getNetworkConfig or just about anything else fails.
    #
    # reloadAll is added as an abort command here so that it runs when any of
    # the set* plans fail and back out.
    update.plans.addPlans(plangraph.STRUCT_GET_SYSTEM_DEVICES,
                          (devices.getSystemDevices, ),
                          (network.abortNetworkConfig, ))
    update.plans.addPlans(plangraph.CHECK_SYSTEM_DEVICES,
                          (devices.checkSystemDevices, ))
    update.plans.addPlans(plangraph.STRUCT_SET_SYSTEM_DEVICES,
                          (devices.setSystemDevices, ),
                          (configservice.reloadAll, ))

    update.plans.addPlans(plangraph.STRUCT_GET_HOST_CONFIG,
                          (hostconfig.getHostConfig, ))
    update.plans.addPlans(plangraph.STRUCT_SET_HOST_CONFIG,
                          (hostconfig.setHostConfig, ),
                          (hostconfig.revertHostConfig, ))

    # Save current network configuration into chute cache (key: 'networkInterfaces')
    update.plans.addPlans(plangraph.STRUCT_GET_INT_NETWORK,
                          (network.getNetworkConfig, ))


    # Reload configuration files
    todoPlan = (configservice.reloadAll, )
    abtPlan = [(osconfig.revertConfig, "dhcp"),
               (osconfig.revertConfig, "firewall"),
               (osconfig.revertConfig, "network"),
               (osconfig.revertConfig, "wireless"),
               (configservice.reloadAll, )]
    update.plans.addPlans(plangraph.RUNTIME_RELOAD_CONFIG, todoPlan, abtPlan)
