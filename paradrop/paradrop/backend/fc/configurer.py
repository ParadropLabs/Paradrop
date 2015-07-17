###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import time, threading

from paradrop.lib.utils.output import out, logPrefix
from paradrop.lib.utils.pdutils import timeint, str2json

from paradrop.lib import settings

from . import updateObject

class PDConfigurer:
    """
        ParaDropConfigurer class.
        This class is in charge of making the configuration changes required on the chutes.
        It utilizes the ChuteStorage class to hold onto the chute data.

        Use @updateChutes to make the configuration changes on the AP.
            This function is thread-safe, this class will only call one update set at a time.
            All others are held in a queue until the last update is complete.
    """
    def __init__(self, storage, lclReactor):
        self.storage = storage
        self.reactor = lclReactor

        self.updateLock = threading.Lock()
        self.updateQueue = []

        ###########################################################################################
        # Launch the first update call, NOTE that you have to use callInThread!!
        # This happens because the performUpdates should run in its own thread,
        # it makes blocking calls and such... so if we *don't* use callInThread
        # then this function WILL BLOCK THE MAIN EVENT LOOP (ie. you cannot send any data)
        ###########################################################################################
        self.reactor.callInThread(self.performUpdates)
    
    def getNextUpdate(self):
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
    
    def clearUpdateList(self):
        """MUTEX: updateLock
            Clears all updates from list (new array).
        """
        self.updateLock.acquire()
        self.updateQueue = []
        self.updateLock.release()
    
    def updateList(self, **updateObj):
        """MUTEX: updateLock
            Take the list of Chutes and push the list into a queue object, this object will then call
            the real update function in another thread so the function that called us is not blocked.
            
            We take a callable responseFunction to call, when we are done with this update we should call it."""
        self.updateLock.acquire()
        # Push the data into our update queue
        self.updateQueue.append(updateObj)
        self.updateLock.release()
            
    def performUpdates(self):
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
        # Always perform this work
        while(self.reactor.running):
            # Check for new updates
            updateObj = self.getNextUpdate()
            if(updateObj is None):
                time.sleep(1)
                continue
            
            try:
                # Take the object and identify the update type
                update = updateObject.parse(updateObj)
                out.info('Performing update %s\n' % (update))

                # TESTING start
                if(settings.FC_BOUNCE_UPDATE):
                    out.testing('Bouncing update %s, result: %s\n' % (
                        update, settings.FC_BOUNCE_UPDATE))
                    update.complete(success=True, message=settings.FC_BOUNCE_UPDATE)
                    continue
                # TESTING end

                # Based on each update type execute could be different
                update.execute()

            except Exception as e:
                out.exception(e, True)

    
