import json

from klein import Klein

from paradrop.base import pdutils
from . import cors


class ChangeApi(object):
    routes = Klein()

    def __init__(self, update_manager):
        self.update_manager = update_manager

    @routes.route('/', methods=['GET'])
    def get_changes(self, request):
        """
        Get list of active and queued changes.

        Note: we use the term "change" even though, internally, the objects are
        referred to as "updates". The word "update" has become so overloaded it
        causes much confusion. A "change" is an atomic and self-contained
        alteration to the running state of the system. A "change" could install
        a chute, remove a chute, change the host configuration, etc.
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        changes = []

        def dump_update(update, status):
            result = {
                'id': update.change_id,
                'updateClass': update.updateClass,
                'updateType': update.updateType,
                'user': update.user.__dict__,
                'name': getattr(update, 'name', None),
                'version': getattr(update, 'version', None),
                'status': status
            }
            return result

        for update in self.update_manager.active_changes.values():
            changes.append(dump_update(update, 'processing'))

        for update in self.update_manager.updateQueue:
            changes.append(dump_update(update, 'queued'))

        return json.dumps(changes)

    @routes.route('/', methods=['POST'])
    def create_change(self, request):
        """
        Schedule a new change.

        Note: we use the term "change" even though, internally, the objects are
        referred to as "updates". The word "update" has become so overloaded it
        causes much confusion. A "change" is an atomic and self-contained
        alteration to the running state of the system. A "change" could install
        a chute, remove a chute, change the host configuration, etc.
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        change = json.loads(request.content.read())
        change['tok'] = pdutils.timeint()

        # We will return the change ID to the caller for tracking and log
        # retrieval.
        change['change_id'] = self.update_manager.assign_change_id()

        self.update_manager.add_update(**change)

        result = {
            'change_id': change['change_id']
        }
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(result)
