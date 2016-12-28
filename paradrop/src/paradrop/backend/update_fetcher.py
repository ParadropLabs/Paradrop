'''
Fetch new updates from the pdserver and apply the updates
'''

import json

from twisted.internet import reactor, task
from twisted.internet.defer import Deferred, inlineCallbacks

from paradrop.lib.misc.reporting import sendStateReport
from paradrop.lib.utils.http import PDServerRequest
from paradrop.base import settings
from paradrop.base.output import out
from paradrop.base.pdutils import timeint


# Interval (in seconds) for polling the server for updates.  This is a fallback
# in case the notifications over WAMP fail, so it can be relatively infrequent.
#
# The automatic polling does not start until after pull_update()
# has been called at least once.
UPDATE_POLL_INTERVAL = 15 * 60


class UpdateFetcher(object):
    def __init__(self):
        # Store set of update IDs that are in progress in order to avoid
        # repeats.
        self.updates_in_progress = set()


    def start_polling(self):
        self.scheduled_call = task.LoopingCall(self.pull_update, _auto=True)


    @inlineCallbacks
    def pull_update(self, _auto=False):
        """
        Start updates by polling the server for the latest updates.

        This is the only method that needs to be called from outside.  The rest
        are triggered asynchronously.

        Call chain:
        pull_update -> _updates_received -> _update_complete

        _auto: Set to True when called by the scheduled LoopingCall.
        """
        # If this call was triggered externally (_auto=False), then reset the
        # timer for the next scheduled call so we do not poll again too soon.
        if not _auto and self.scheduled_call.running:
            self.scheduled_call.reset()

        def handle_error(error):
            print("Request for updates failed: {}".format(error.getErrorMessage()))

        request = PDServerRequest('/api/routers/{router_id}/updates')
        d = request.get(completed=False)
        d.addCallback(self._updates_received)
        d.addErrback(handle_error)

        yield d

        # Make sure the LoopingCall is scheduled to run later.
        if not self.scheduled_call.running:
            self.scheduled_call.start(UPDATE_POLL_INTERVAL, now=False)


    @inlineCallbacks
    def _updates_received(self, response):
        if not response.success or response.data is None:
            print("There was an error receiving updates from the server.")
            return

        updates = response.data
        print("Received {} update(s) from server.".format(len(updates)))

        # Remove old updates from the set of in progress updates.  These are
        # updates that the server is no longer sending to us.
        received_set = set(item['_id'] for item in updates)
        old_updates = self.updates_in_progress - received_set
        self.updates_in_progress -= old_updates

        for item in updates:
            # TODO: Handle updates with started=True very carefully.
            #
            # There are at least two interesting cases:
            # 1. We started an update but crashed or rebooted without
            # completing it.
            # 2. We started an upgrade to paradrop, the daemon was just
            # restarted, but pdinstall has not reported that the update is
            # complete yet.
            #
            # If we skip updates with started=True, we will not retry updates
            # in case #1.
            if item['_id'] in self.updates_in_progress or item.get('started', False):
                continue
            else:
                self.updates_in_progress.add(item['_id'])

            update = dict(updateClass=item['updateClass'],
                          updateType=item['updateType'],
                          tok=timeint())

            # Save fields that relate to external management of this chute.
            update['external'] = {
                'update_id': item['_id'],
                'chute_id': item.get('chute_id', None),
                'version_id': item.get('version_id', None)
            }

            # Backend might send us garbage; be sure that we only accept the
            # config field if it is present and is a dict.
            config = item.get('config', {})
            if isinstance(config, dict):
                update.update(config)

            yield update_manager.add_update(**update)
            yield _update_complete(update)

        out.log("All updates complete, sending state report to server...")
        sendStateReport()

    
    def _update_complete(self, update):
        """
        Internal: callback after an update operation has been completed
        (successfuly or otherwise) and send a notification to the server.
        """
        # If delegated to an external program, we do not report to pdserver
        # that the update is complete.
        if update.delegated:
            return

        update_id = update.external['update_id']
        success = update.result.get('success', False)

        request = PDServerRequest('/api/routers/{router_id}/updates/' +
                str(update_id))
        d = request.patch(
            {'op': 'replace', 'path': '/completed', 'value': True},
            {'op': 'replace', 'path': '/success', 'value': success}
        )

        # TODO: If this notification fails to go through, we should retry or
        # build in some other mechanism to inform the server.
        #
        # Not catching errors here so we see a stack trace if there is an
        # error.  This is an omission that will need to be dealt with.
