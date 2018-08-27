###################################################################
# Copyright 2013-2016 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.base.output import out
from paradrop.core.chute.chute import Chute
from paradrop.core.config import state
from paradrop.core.container import dockerapi

from . import plangraph


def validate_change(update):
    """
    Check if the update is a valid change.
    """
    requires_old = ['stop', 'start', 'delete', 'restart']
    requires_no_old = ['create']

    if update.old is None and update.updateType in requires_old:
        update.failure = "No chute found with id: " + update.name
        return False

    if update.old is not None and update.updateType in requires_no_old:
        update.failure = "Chute already exists."
        return False

    if update.new.state == Chute.STATE_INVALID:
        update.failure = "Chute state is invalid."
        return False

    if update.updateType == "start" and update.old.isRunning():
        update.failure = "Chute is already running."
        return False

    if update.updateType == "stop" and not update.old.isRunning():
        update.failure = "Chute is already stopped."
        return False

    if update.old is None:
        old_version = 0
    else:
        old_version = update.old.version

    if update.updateType == "update" and update.new.version <= old_version:
        update.failure = "Version {} of the chute is already installed.".format(
            old_version)
        return False

    return True


def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))

    # Check for some error conditions that we can detect during the planning
    # stage, e.g. starting a chute that does not exist.
    if not validate_change(update):
        return True

    update.plans.addPlans(plangraph.STATE_GENERATE_SERVICE_PLANS,
                          (generate_service_plans, ))

    if update.new.isRunning():
        update.plans.addPlans(plangraph.STATE_NET_START,
                              (dockerapi.setup_net_interfaces, ),
                              (dockerapi.cleanup_net_interfaces, ))

        if update.old is None:
            update.plans.addPlans(plangraph.STATE_CREATE_BRIDGE,
                                  (dockerapi.create_bridge, ),
                                  (dockerapi.remove_bridge, ))

    if update.old is not None and update.old.isRunning():
        update.plans.addPlans(plangraph.STATE_NET_STOP,
                              (dockerapi.cleanup_net_interfaces, ),
                              (dockerapi.setup_net_interfaces, ))

    if update.updateType == "delete":
        update.plans.addPlans(plangraph.STATE_REMOVE_BRIDGE,
                              (dockerapi.remove_bridge, ),
                              (dockerapi.create_bridge, ))

    # Save the chute to the chutestorage.
    update.plans.addPlans(plangraph.STATE_SAVE_CHUTE, (state.saveChute, ),
                          (state.revertChute, ))

    return None


def generate_service_plans(update):
    """
    Generate plans that depend on the services configured for the chute.

    This needs to happen after the chute configuration has been parsed.
    """
    for service in update.new.get_services():
        if update.updateType in ["create", "update"]:
            update.plans.addPlans(plangraph.STATE_BUILD_IMAGE,
                                  (dockerapi.prepare_image, service),
                                  (dockerapi.remove_image, service))

            update.plans.addPlans(plangraph.STATE_CHECK_IMAGE,
                                  (dockerapi.check_image, service))

        if update.new.isRunning():
            update.plans.addPlans(plangraph.STATE_CALL_START,
                                  (dockerapi.start_container, service),
                                  (dockerapi.remove_container, service))

    old_services = []
    if update.old is not None:
        old_services = update.old.get_services()

    for service in old_services:
        if update.old.isRunning():
            update.plans.addPlans(plangraph.STATE_CALL_STOP,
                                  (dockerapi.remove_container, service),
                                  (dockerapi.start_container, service))

        if update.updateType in ["update", "delete"]:
            update.plans.addPlans(plangraph.STATE_CALL_CLEANUP,
                                  (dockerapi.remove_image, service))
