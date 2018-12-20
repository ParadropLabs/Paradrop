###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import time
import threading
from twisted.internet import defer, threads

from paradrop.base.output import out
from paradrop.base.pdutils import timeint
from paradrop.base import constants, nexus, settings
from paradrop.core.agent import reporting
from paradrop.lib.misc.procmon import dockerMonitor, containerdMonitor
from paradrop.core.chute.restart import reloadChutes

from . import update_object


class UpdateManager:

    """
        This class is in charge of making the configuration changes required on the chutes.
        It utilizes the ChuteStorage class to hold onto the chute data.

        Use @updateChutes to make the configuration changes on the AP.
            This function is thread-safe, this class will only call one update set at a time.
            All others are held in a queue until the last update is complete.
    """

    def __init__(self, reactor):
        self.reactor = reactor

        self.updateLock = threading.Lock()
        self.updateQueue = []

        # Map update_id -> update object.
        self.active_changes = {}

        # TODO: Ideally, load this from file so that change IDs are unique
        # across system reboots.
        self.next_change_id = 1

        ###########################################################################################
        # Launch the first update call, NOTE that you have to use callInThread!!
        # This happens because the perform_updates should run in its own thread,
        # it makes blocking calls and such... so if we *don't* use callInThread
        # then this function WILL BLOCK THE MAIN EVENT LOOP (ie. you cannot send any data)
        #
        # FIXME: It should be noted that calling updateLock.acquire(), e.g.
        # from add_update, also blocks the main thread.  Synchronizing access
        # to the work queue should be reworked.
        ###########################################################################################
        self.reactor.callInThread(self._perform_updates)

    def _get_next_update(self):
        """MUTEX: updateLock
            Returns the size of the local update queue.
        """
        self.updateLock.acquire()
        if(len(self.updateQueue) > 0):
            # Get first available
            a = self.updateQueue.pop(0)
        else:
            a = None
        self.updateLock.release()
        return a

    def clear_update_list(self):
        """MUTEX: updateLock
            Clears all updates from list (new array).
        """
        self.updateLock.acquire()
        self.updateQueue = []
        self.updateLock.release()

    def add_update(self, **update):
        """MUTEX: updateLock
            Take the list of Chutes and push the list into a queue object, this object will then call
            the real update function in another thread so the function that called us is not blocked.

            We take a callable responseFunction to call, when we are done with this update we should call it.
        """
        d = defer.Deferred()
        update['deferred'] = d

        # Make sure the update object has a change ID for message retrieval.  Some
        # code paths (API code) will prefer to set the change ID before calling
        # add_update so that they can return the change ID to the user.
        if 'change_id' not in update:
            update['change_id'] = self.assign_change_id()

        # Convert to Update object before storing.
        updateObj = update_object.parse(update)

        self.updateLock.acquire()
        self.updateQueue.append(updateObj)
        self.updateLock.release()

        return d

    def add_provision_update(self, hostconfig_patch, zerotier_networks):
        update = self._make_router_update("patchhostconfig")
        update.patch = list(hostconfig_patch)

        for network in zerotier_networks:
            update.patch.append({
                "op": "add",
                "path": "/zerotier/networks/-",
                "value": network
            })

        self.updateQueue.append(update)

    def assign_change_id(self):
        """
        Get a unique change ID for an update.

        This should be used to set the change_id field in an update object.
        """
        x = self.next_change_id
        self.next_change_id += 1
        return x

    def find_change(self, change_id):
        """
        Search active and queued changes for the requested change.

        Returns an Update object or None.
        """
        if change_id in self.active_changes:
            return self.active_changes[change_id]

        for update in self.updateQueue:
            if update.change_id == change_id:
                return update

        return None

    def _make_router_update(self, updateType):
        """
        Make a ROUTER class update object.
        """
        update = dict(updateClass='ROUTER',
                    updateType=updateType,
                    name=constants.RESERVED_CHUTE_NAME,
                    tok=timeint())
        return update_object.parse(update)

    def _perform_updates(self):
        """This is the main working function of the PDConfigurer class.
            It should be executed as a separate thread, it does the following:
                checks for any updates to perform
                does them
                responds to the server
                removes the update
                checks for more updates
                    if more exist it calls itself again more quickly
                    else it puts itself to sleep for a little while
        """
        if settings.CHECK_DOCKER:
            ready = dockerMonitor.ensureReady()
            if not ready:
                out.warn("Docker does not appear to be running.  "
                            "Most functionality with containers will be broken.")

            ready = containerdMonitor.ensureReady()
            if not ready:
                out.warn("Docker containerd does not appear to be running.  "
                            "Most functionality with containers will be broken.")

        # add any chutes that should already be running to the front of the
        # update queue before processing any updates
        startQueue = reloadChutes()
        self.updateLock.acquire()
        self.updateQueue.append(self._make_router_update("prehostconfig"))
        self.updateQueue.append(self._make_router_update("inithostconfig"))
        self.updateQueue.extend(startQueue)
        self.updateLock.release()

        # Always perform this work
        while self.reactor.running:
            # Check for new updates
            change = self._get_next_update()
            if change is None:
                time.sleep(1)
                continue

            self._perform_update(change)

            # Apply a batch of updates and when the queue is empty, send a
            # state report.  We're not reacquiring the mutex here because the
            # worst case is we send out an extra state update.
            if len(self.active_changes) == 0 and nexus.core.provisioned():
                threads.blockingCallFromThread(self.reactor,
                        reporting.sendStateReport)

    def _perform_update(self, update):
        """
        Perform a single update, to be called by perform_updates.

        This is split from perform_updates for easier unit testing.
        """
        # Add to the active set when processing starts. It is a dictionary, so
        # it does not matter if this is the first time we see this update or
        # if we are resuming it.
        self.active_changes[update.change_id] = update

        try:
            # Mark update as having been started.
            update.started()
            out.info('Performing update %s\n' % (update))

            # TESTING start
            # TODO: still need this?
            if(settings.FC_BOUNCE_UPDATE): # pragma: no cover
                out.testing('Bouncing update %s, result: %s\n' % (
                    update, settings.FC_BOUNCE_UPDATE))
                update.complete(success=True, message=settings.FC_BOUNCE_UPDATE)
                return
            # TESTING end

            # Based on each update type execute could be different
            result = update.execute()
            if isinstance(result, defer.Deferred):
                # Update is not done, but it is yielding. When the deferred
                # fires, add it back to the work queue to resume it.
                #
                # TODO: We could handle errors separately and use that to break
                # the update pipeline, but then we need to propagate that
                # through the update.execute, executionplan chain.  For now,
                # we have an update stage right after prepare_image that checks
                # if the build was successful or throws an exception. That
                # should work but is not very general.
                def resume(result):
                    self.updateQueue.append(update)
                result.addBoth(resume)
            elif update.change_id in self.active_changes:
                # Update is done, so remove it from the active list.
                del self.active_changes[update.change_id]

        except Exception as e:
            out.exception(e, True)
