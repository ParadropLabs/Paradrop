'''
Fetch new updates from the pdserver and apply the updates
'''
from __future__ import print_function

from twisted.internet import task
from twisted.internet.defer import inlineCallbacks

from paradrop.core.agent.http import PDServerRequest
from paradrop.core.auth.user import User
from paradrop.base.output import out
from paradrop.base.pdutils import timeint


# Interval (in seconds) for polling the server for updates.  This is a fallback
# in case the notifications over WAMP fail, so it can be relatively infrequent.
#
# The automatic polling does not start until after pull_update()
# has been called at least once.
UPDATE_POLL_INTERVAL = 15 * 60


class UpdateFetcher(object):
    def __init__(self, update_manager):
        # Store set of update IDs that are in progress in order to avoid
        # repeats.
        self.updates_in_progress = set()
        self.update_manager = update_manager
        self.scheduled_call = task.LoopingCall(self.pull_update, _auto=True)

        self.long_poll_started = False
        self.use_long_poll = True

    @inlineCallbacks
    def start_long_poll(self):
        self.long_poll_started = True

        while self.use_long_poll:
            request = PDServerRequest('/api/routers/{router_id}/updates/poll')
            try:
                response = yield request.get()
            except Exception:
                pass
            else:
                # 200 = update(s) available
                # 204 = no updates yet
                # 404 = server does not support this endpoint
                if response.code == 200:
                    self.pull_update(_auto=False)
                elif response.code == 404:
                    self.use_long_poll = False

    def start_polling(self):
        # Long polling is a more recent addition. If the server supports it, it
        # will only respond to our GET request after an update is available or a
        # timeout has expired.
        if not self.long_poll_started:
            self.start_long_poll()

        # Basic polling is our baseline. It always works with no dependency on
        # maintaining websocket connections, etc. Set the polling interval to
        # something reasonable, e.g. 15 minutes to 1 hour.
        if not self.scheduled_call.running:
            self.scheduled_call.start(UPDATE_POLL_INTERVAL, now=False)

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
            if item['_id'] in self.updates_in_progress:
                continue
            elif item.get('started', False):
                yield self._update_ignored(item)
                continue
            else:
                self.updates_in_progress.add(item['_id'])

            creator = item.get('creator', {})
            username = creator.get("name", "paradrop")
            role = creator.get("access_level", "trusted")

            update = dict(updateClass=item['updateClass'],
                          updateType=item['updateType'],
                          user=User(username, "paradrop.org", role=role),
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

            update = yield self.update_manager.add_update(**update)
            yield self._update_complete(update)


    def _update_complete(self, update):
        """
        Internal: callback after an update operation has been completed
        (successfuly or otherwise) and send a notification to the server.
        """
        # If delegated to an external program, we do not report to pdserver
        # that the update is complete.
        if update.delegated:
            return

        out.info("The update is done, report it to server...")
        update_id = update.external['update_id']
        success = update.result.get('success', False)

        request = PDServerRequest('/api/routers/{router_id}/updates/' +
                str(update_id))
        d = request.patch(
            {'op': 'replace', 'path': '/completed', 'value': True},
            {'op': 'replace', 'path': '/success', 'value': success}
        )

        return d

        # TODO: If this notification fails to go through, we should retry or
        # build in some other mechanism to inform the server.
        #
        # Not catching errors here so we see a stack trace if there is an
        # error.  This is an omission that will need to be dealt with.

    def _update_ignored(self, update):
        """
        Internal: callback for an update that we are ignoring because
        it was started previously and never completed.
        """
        update_id = update['_id']
        request = PDServerRequest('/api/routers/{router_id}/updates/' +
                str(update_id))
        d = request.patch(
            {'op': 'replace', 'path': '/completed', 'value': True},
            {'op': 'replace', 'path': '/success', 'value': False}
        )
        return d
