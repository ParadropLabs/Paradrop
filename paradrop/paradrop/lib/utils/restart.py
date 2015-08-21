####################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

'''
lib.utils.restart
Contains the functions required to restart chutes properly on power cycle of device.
Checks with pdconfd to make sure it was able to properly bring up all interfaces before
starting chutes.
'''

from pdtools.lib.output import out
from paradrop.backend.fc import chutestorage
from pdtools.lib.pdutils import json2str, str2json, timeint, urlDecodeMe
from paradrop.backend.pdconfd.client import waitSystemUp
from paradrop.lib import chute, settings
from paradrop.lib.config.network import reclaimNetworkResources
import time

FAILURE_WARNING = """
    ************************WARNING************************
    This chute failed to start on a previous attempt for some reason. 
    Perhaps hardware on the device has changed? 
    The chute has been stopped and will need to be started.
    """

def reloadChutes():
    """
    This function is called to restart any chutes that were running prior to the system being restarted.
    It waits for pdconfd to come up and report whether or not it failed to bring up any of the interfaces
    that existed before the power cycle. If pdconfd indicates something failed we then force a stop update
    in order to bring down all interfaces associated with that chute and mark it with a warning. 
    If the stop fails we mark the chute with a warning manually and change its state to stopped and save to 
    storage this isn't great as it could mean our system still has interfaces up associated with that chute.
    If pdconfd doesn't report failure we attempt to start the chute and if this fails we trust the abort process
    to restore the system to a consistent state and we manually mark the chute as stopped and add a warning to it.
    :param None
    :returns: (list) A list of update dicts to be used to create updateObjects that should be run before accepting new updates.
    """
    if not settings.PDCONFD_ENABLED:
        return []
    chuteStore = chutestorage.ChuteStorage()
    chutes = [ ch for ch in chuteStore.getChuteList() if ch.state == 'running']

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
        confdInfo = str2json(confdInfo)

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
            if failedChuteName == settings.RESERVED_CHUTE:
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

    #First stop all chutes that failed to bring up interfaces according to
    #pdconfd then start successful ones #We do this because pdfcd needs to
    #handle cleaning up uci files and then tell pdconfd
    updates = []
    for ch in failedChutes:
        updates.append(dict(updateClass='CHUTE', updateType='stop', name=ch,
                       tok=timeint(), func=updateStatus,
                       warning=FAILURE_WARNING))

    for ch in okChutes:
        updates.append(dict(updateClass='CHUTE', updateType='restart', name=ch,
                       tok=timeint(), func=updateStatus))

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
    chuteStore = chutestorage.ChuteStorage()
    if not update.result.get('success'):
        update.old.state = 'stopped'
        update.old.warning = FAILURE_WARNING
        chuteStore.saveChute(update.old)
