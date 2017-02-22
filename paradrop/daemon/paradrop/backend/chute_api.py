import json
from klein import Klein
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

from paradrop.base import pdutils
from paradrop.base.output import out
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.config import resource
from paradrop.core.container.chutecontainer import ChuteContainer
from . import cors


class UpdateEncoder(json.JSONEncoder):
    def default(self, o):
        result = {
            'created': o.createdTime,
            'responses': o.responses,
            'failure': o.failure
        }
        return result


class ChuteApi(object):
    routes = Klein()

    def __init__(self, update_manager):
        self.update_manager = update_manager

    @routes.route('/get')
    def get_chutes(self, request):
        out.info('Get chute list')
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        chuteStorage = ChuteStorage()
        chutes = chuteStorage.getChuteList()
        allocation = resource.computeResourceAllocation(chutes)

        result = []
        for chute in chutes:
            container = ChuteContainer(chute.name)

            result.append({
                'name': chute.name,
                'state': container.getStatus(),
                'version': getattr(chute, 'version', None),
                'allocation': allocation.get(chute.name, None),
                'environment': getattr(chute, 'environment', None),
                'resources': getattr(chute, 'resources', None)
            })

        return json.dumps(result)

    @routes.route('/create', methods=['POST'])
    @inlineCallbacks
    def create_chute(self, request):
        out.info('Creating chute...')

        cors.config_cors(request)
        body = json.loads(request.content.read())
        config = body['config']

        update = dict(updateClass='CHUTE',
                      updateType='create',
                      tok=pdutils.timeint())
        update.update(config)
        result = yield self.update_manager.add_update(**update)

        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))


    @routes.route('/update', methods=['PUT'])
    @inlineCallbacks
    def update_chute(self, request):
        out.info('Creating chute...')

        cors.config_cors(request)
        body = json.loads(request.content.read())
        config = body['config']

        update = dict(updateClass='CHUTE',
                      updateType='udpate',
                      tok=pdutils.timeint())
        update.update(config)
        result = yield self.update_manager.add_update(**update)

        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))


    @routes.route('/delete', methods=['DELETE'])
    @inlineCallbacks
    def delete_chute(self, request):
        out.info('Creating chute...')

        cors.config_cors(request)
        body = json.loads(request.content.read())
        config = body['config']

        update = dict(updateClass='CHUTE',
                      updateType='delete',
                      tok=pdutils.timeint())
        update.update(config)
        result = yield self.update_manager.add_update(**update)

        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))


    @routes.route('/stop', methods=['PUT'])
    @inlineCallbacks
    def stop_chute(self, request):
        out.info('Creating chute...')

        cors.config_cors(request)
        body = json.loads(request.content.read())
        config = body['config']

        update = dict(updateClass='CHUTE',
                      updateType='stop',
                      tok=pdutils.timeint())
        update.update(config)
        result = yield self.update_manager.add_update(**update)

        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))


    @routes.route('/start', methods=['PUT'])
    @inlineCallbacks
    def start_chute(self, request):
        out.info('Creating chute...')

        cors.config_cors(request)
        body = json.loads(request.content.read())
        config = body['config']

        update = dict(updateClass='CHUTE',
                      updateType='start',
                      tok=pdutils.timeint())
        update.update(config)
        result = yield self.update_manager.add_update(**update)

        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))
