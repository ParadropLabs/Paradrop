###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from pdtools.lib.output import out
from paradrop.backend.exc import plangraph
from paradrop.lib import chute, settings
from pdtools.lib.pdutils import jsonPretty

from paradrop.lib.utils import dockerapi as virt


def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))

    # If this chute is new (no old version)
    if(update.old is None):
        out.verbose('new chute\n')

        # If it's a stop, start, delete, or restart command go ahead and fail right now since we don't have a record of it
        if update.updateType in ['stop', 'start', 'delete', 'restart']:
            update.failure = "No chute found with id: " + update.name
            return True
        # If we are now running then everything has to be setup for the first time
        if(update.new.state == chute.STATE_RUNNING):
            update.plans.addPlans(plangraph.STATE_CALL_START, (virt.startChute,))

        # Check if the state is invalid, we should return bad things in this case (don't do anything)
        elif(update.new.state == chute.STATE_INVALID):
            if(settings.DEBUG_MODE):
                update.responses.append('Chute state is invalid')
            return True

    # Not a new chute
    else:
        if update.updateType == 'start':
            if update.old.state == chute.STATE_RUNNING:
                update.failure = update.name + " already running."
                return True
            update.plans.addPlans(plangraph.STATE_CALL_START, (virt.restartChute,))
        elif update.updateType == 'restart':
            update.plans.addPlans(plangraph.STATE_CALL_START, (virt.restartChute,))
        elif update.updateType == 'create':
            update.failure = update.name + " already exists on this device."
            return True
        elif update.new.state == chute.STATE_STOPPED:
            if update.updateType == 'delete':
                update.plans.addPlans(plangraph.STATE_CALL_STOP, (virt.removeChute,))
            if update.updateType == 'stop':
                if update.old.state == chute.STATE_STOPPED:
                    update.failure = update.name + " already stopped."
                    return True
                update.plans.addPlans(plangraph.STATE_CALL_STOP, (virt.stopChute,))

    return None
