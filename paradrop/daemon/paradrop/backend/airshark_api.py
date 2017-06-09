'''
APIs for developers to check whether Airshark feature is available or not
'''
import json
from klein import Klein

from paradrop.lib.utils import pdos

from . import cors


class AirsharkApi:
    routes = Klein()

    def __init__(self, airshark_manager):
        self.airshark_manager = airshark_manager

    @routes.route('/status')
    def status(self, request):
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        hardware_ready, software_ready, scanner_running \
            = self.airshark_manager.status()
        data = dict()
        data['hardware_ready'] = hardware_ready
        data['software_ready'] = software_ready
        data['scanner_running'] = scanner_running
        return json.dumps(data)
