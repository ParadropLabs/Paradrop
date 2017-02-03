import json
from klein import Klein
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

from paradrop.base.output import out
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.config import resource
from paradrop.core.container.chutecontainer import ChuteContainer
from . import cors

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
        body = str2json(request.content.read())
        config = body['config']

        if config:
            update = dict(updateClass='CHUTE',
                          updateType='create',
                          tok=timeint())
            update.update(config)
            result = yield self.update_manager.add_update(**update)

            request.setHeader('Content-Type', 'application/json')
            returnValue(json.dumps(result))
        else:
            returnValue(None)


    @routes.route('/update', methods=['PUT'])
    @inlineCallbacks
    def update_chute(self, request):
        out.info('Creating chute...')

        cors.config_cors(request)
        body = str2json(request.content.read())
        config = body['config']

        if config:
            update = dict(updateClass='CHUTE',
                          updateType='udpate',
                          tok=timeint())
            update.update(config)
            result = yield self.update_manager.add_update(**update)

            request.setHeader('Content-Type', 'application/json')
            returnValue(json.dumps(result))
        else:
            returnValue(None)


    @routes.route('/delete', methods=['DELETE'])
    @inlineCallbacks
    def update_chute(self, request):
        out.info('Creating chute...')

        cors.config_cors(request)
        body = str2json(request.content.read())
        config = body['config']

        if config:
            update = dict(updateClass='CHUTE',
                          updateType='delete',
                          tok=timeint())
            update.update(config)
            result = yield self.update_manager.add_update(**update)

            request.setHeader('Content-Type', 'application/json')
            returnValue(json.dumps(result))
        else:
            returnValue(None)


    @routes.route('/stop', methods=['PUT'])
    @inlineCallbacks
    def update_chute(self, request):
        out.info('Creating chute...')

        cors.config_cors(request)
        body = str2json(request.content.read())
        config = body['config']

        if config:
            update = dict(updateClass='CHUTE',
                          updateType='stop',
                          tok=timeint())
            update.update(config)
            result = yield self.update_manager.add_update(**update)

            request.setHeader('Content-Type', 'application/json')
            returnValue(json.dumps(result))
        else:
            returnValue(None)


    @routes.route('/start', methods=['PUT'])
    @inlineCallbacks
    def update_chute(self, request):
        out.info('Creating chute...')

        cors.config_cors(request)
        body = str2json(request.content.read())
        config = body['config']

        if config:
            update = dict(updateClass='CHUTE',
                          updateType='start',
                          tok=timeint())
            update.update(config)
            result = yield self.update_manager.add_update(**update)

            request.setHeader('Content-Type', 'application/json')
            returnValue(json.dumps(result))
        else:
            returnValue(None)
