'''
APIs for developers to check whether Airshark feature is available or not
'''
import json
from klein import Klein

from . import cors


class AirsharkApi(object):
    routes = Klein()

    def __init__(self, airshark_manager):
        self.airshark_manager = airshark_manager

    @routes.route('/status')
    def status(self, request):
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        hardware_ready, software_ready, airshark_running \
            = self.airshark_manager.status()
        data = dict()
        data['hardware_ready'] = hardware_ready
        data['software_ready'] = software_ready
        data['airshark_running'] = airshark_running
        return json.dumps(data)
