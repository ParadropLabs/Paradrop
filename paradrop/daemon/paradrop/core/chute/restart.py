####################################################################
# Copyright 2013-2017 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

'''
Contains the functions required to restart chutes properly on power cycle of device.
Checks with pdconfd to make sure it was able to properly bring up all interfaces before
starting chutes.
'''

import json
import time

from paradrop.base.output import out
from paradrop.base.pdutils import timeint
from paradrop.base import constants, settings
from paradrop.core.auth.user import User
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.config.network import reclaimNetworkResources
from paradrop.core.update.update_object import UpdateChute
from paradrop.confd.client import waitSystemUp



FAILURE_WARNING = """
    ************************WARNING************************
    This chute failed to start on a previous attempt for some reason. 
    Perhaps hardware on the device has changed? 
    The chute has been stopped and will need to be started.
    """

def reloadChutes():
    """
    Get update objects to chutes that should be running at startup.

    This function is called to restart any chutes that were running
    prior to the system being restarted.  It waits for pdconfd to
    come up and report whether or not it failed to bring up any of the
    interfaces that existed before the power cycle. If pdconfd indicates
    something failed we then force a stop update in order to bring down
    all interfaces associated with that chute and mark it with a warning.
    If the stop fails we mark the chute with a warning manually and change
    its state to stopped and save to storage this isn't great as it could
    mean our system still has interfaces up associated with that chute.
    If pdconfd doesn't report failure we attempt to start the chute and
    if this fails we trust the abort process to restore the system to a
    consistent state and we manually mark the chute as stopped and add
    a warning to it.

    :returns: (list) A list of UpdateChute objects that should be run
              before accepting new updates.
    """
    if not settings.PDCONFD_ENABLED:
        return []
    chuteStore = ChuteStorage()
    chutes = [ ch for ch in chuteStore.getChuteList() if ch.isRunning() ]

    # Part of restoring the chute to its previously running state is reclaiming
    # IP addresses, interface names, etc. that it had previously.
    for chute in chutes:
        reclaimNetworkResources(chute)

    #We need to make sure confd is up and all interfaces have been brought up properly
    confdup = False
    while not confdup:
        confdInfo = waitSystemUp()
        if confdInfo == None:
            time.sleep(1)
            continue
        confdup = True
        confdInfo = json.loads(confdInfo)

    #Remove any chutes from the restart queue if confd failed to bring up the
    #proper interfaces
    #
    # At this point, we only care about the chute names, not the full objects.
    # We are using sets of chute names for their O(1) membership test and
    # element uniqueness.
    okChutes = set([ch.name for ch in chutes])
    failedChutes = set()
    for iface in confdInfo:
        if iface.get('success') is False:
            failedChuteName = iface.get('comment')
            if failedChuteName == constants.RESERVED_CHUTE_NAME:
                out.warn('Failed to load a system config section')
            elif failedChuteName in okChutes:
                # This was a chute that we are supposed to restart, but one of
                # its config sections failed to load.
                okChutes.remove(failedChuteName)
                failedChutes.add(failedChuteName)
            elif failedChuteName not in failedChutes:
                # In this case, the name in the comment was not something that
                # we recognize from the chute storage.  Maybe the chute storage
                # file was deleted but not the config files, or someone
                # manually modified the config files.  Anyway, we cannot
                # attempt to stop this chute because the object does not exist,
                # but we can give a warning message.
                out.warn('Failed to load config section for '
                         'unrecognized chute: {}'.format(failedChuteName))

    updates = []

    # There was code here that looped over the failedChutes set and explicitly
    # stopped those chutes.  However, if the cause of the failure was
    # transient, those chutes would remain stopped until manually restarted.
    # It seems better to leave them alone so that we try again next time the
    # system reboots.
    #
    # TODO: We should still record the failure somewhere.

    # Only try to restart the chutes that had no problems during pdconf
    # initialization.
    for ch in okChutes:
        update_spec = dict(updateClass='CHUTE', updateType='restart', name=ch,
                tok=timeint(), func=updateStatus,
                user=User.get_internal_user())
        update = UpdateChute(update_spec, reuse_existing=True)
        updates.append(update)

    return updates

def updateStatus(update):
    """
    This function is a callback for the updates we do upon restarting the system.
    It checks whether or not the update completed successfully and if not it
    changes the state of the chute to stopped and adds a warning.
    :param update: The update object containing information about the chute that was created and whether it was successful or not.
    :type update: obj
    :returns: None
    """
    pass
