###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import time
import threading
from twisted.internet import defer, threads

from paradrop.base.output import out
from paradrop.base.pdutils import timeint, str2json
from paradrop.base import settings
from paradrop.lib.misc import reporting
from paradrop.lib.misc.procmon import dockerMonitor
from paradrop.lib.chute.restart import reloadChutes

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

        ###########################################################################################
        # Launch the first update call, NOTE that you have to use callInThread!!
        # This happens because the perform_updates should run in its own thread,
        # it makes blocking calls and such... so if we *don't* use callInThread
        # then this function WILL BLOCK THE MAIN EVENT LOOP (ie. you cannot send any data)
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

    def add_update(self, **updateObj):
        """MUTEX: updateLock
            Take the list of Chutes and push the list into a queue object, this object will then call
            the real update function in another thread so the function that called us is not blocked.

            We take a callable responseFunction to call, when we are done with this update we should call it.
        """
        d = defer.Deferred()
        updateObj['deferred'] = d

        self.updateLock.acquire()
        self.updateQueue.append(updateObj)
        self.updateLock.release()

        return d

    def _make_hostconfig_update(self):
        """
        Makes an update object for initializing hostconfig.
        """
        return dict(updateClass='ROUTER',
                    updateType='inithostconfig',
                    name='__PARADROP__',
                    tok=timeint())

    def _perform_updates(self, checkDocker=True):
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
        if checkDocker:
            ready = dockerMonitor.ensureReady()
            if not ready:
                out.warn("Docker does not appear to be running.  "
                            "Most functionality with containers will be broken.")

        # add any chutes that should already be running to the front of the
        # update queue before processing any updates
        startQueue = reloadChutes()
        self.updateLock.acquire()
        # insert the data into the front of our update queue so that all old
        # chutes restart before new ones are processed
        for updateObj in startQueue:
            self.updateQueue.insert(0, updateObj)
        # Finally, insert an update that initializes the hostconfig.
        # This should happen before everything else.
        self.updateQueue.insert(0, self._make_hostconfig_update())
        self.updateLock.release()

        # Always perform this work
        while(self.reactor.running):
            # Check for new updates
            updateObj = self._get_next_update()
            if(updateObj is None):
                time.sleep(1)
                continue

            self._perform_update(updateObj)

            # Apply a batch of updates and when the queue is empty, send a
            # state report.  We're not reacquiring the mutex here because the
            # worst case is we send out an extra state update.
            if len(self.updateQueue) == 0:
                threads.blockingCallFromThread(self.reactor,
                        reporting.sendStateReport)

    def _perform_update(self, updateObj):
        """
        Perform a single update, to be called by perform_updates.

        This is split from perform_updates for easier unit testing.
        """
        try:
            # Take the object and identify the update type
            update = update_object.parse(updateObj)

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
            update.execute()

        except Exception as e:
            out.exception(e, True)
