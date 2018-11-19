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
from paradrop.core.config import airshark, devices, haproxy, network, configservice, hostconfig, reservations, services, zerotier

from . import plangraph


# Update types that apply changes from host configuration.
CONFIG_CHANGING_TYPES = set([
    "inithostconfig",
    "sethostconfig",
    "patchhostconfig"
])


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

    update.plans.addPlans(plangraph.STRUCT_GET_RESERVATIONS,
                          (reservations.getReservations, ))

    update.plans.addPlans(plangraph.STRUCT_GET_HOST_CONFIG,
                          (hostconfig.getHostConfig, ))

    # Save current network configuration into chute cache (key: 'networkInterfaces')
    update.plans.addPlans(plangraph.STRUCT_GET_INT_NETWORK,
                          (network.getNetworkConfig, ))

    # Start haproxy.  This does not depend on the host config, and we want
    # it setup even in cases where applying the host config failed.
    update.plans.addPlans(plangraph.RECONFIGURE_PROXY,
                          (haproxy.reconfigureProxy, ))

    if update.updateType in CONFIG_CHANGING_TYPES:
        # Save current host configuration to disk.
        update.plans.addPlans(plangraph.STRUCT_SET_HOST_CONFIG,
                              (hostconfig.setHostConfig, ),
                              (hostconfig.revertHostConfig, ))

        # Apply host configuration to system configuration.
        update.plans.addPlans(plangraph.STRUCT_SET_SYSTEM_DEVICES,
                              (devices.setSystemDevices, ),
                              (configservice.reloadAll, ))

        # Apply zerotier configuration.
        update.plans.addPlans(plangraph.ZEROTIER_CONFIGURE,
                              (zerotier.configure, ))

        # Apply Airshark configuration.
        update.plans.addPlans(plangraph.AIRSHARK_CONFIGURE,
                              (airshark.configure, ))

        # Configure telemetry service.
        update.plans.addPlans(plangraph.TELEMETRY_SERVICE,
                              (services.configure_telemetry, ))

        # Reload configuration files
        todoPlan = (configservice.reloadAll, )
        update.plans.addPlans(plangraph.RUNTIME_RELOAD_CONFIG, todoPlan)

        # Reload configuration files if aborting.  This needs to happen at the
        # right place in the update pipeline such that UCI files have been
        # restored to their previous contents.
        todoPlan = (configservice.reload_placeholder, )
        abtPlan = (configservice.reloadAll, )
        update.plans.addPlans(plangraph.RUNTIME_RELOAD_CONFIG_BACKOUT, todoPlan, abtPlan)
