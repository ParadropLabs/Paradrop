'''
APIs for developers to check whether Airshark feature is available or not
'''
import json
from klein import Klein

from paradrop.lib.utils import pdos
from . import cors


class InformationApi:
    routes = Klein()

    def __init__(self):

    @routes.route('/status')
    def status(self, request):
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        data = dict()
        #
        # "not available"
        # "error"
        # "running"
        #
        data['status'] = 'not available'
        return json.dumps(data)
