'''
Provide information of the router, e.g. board version, CPU information,
memory size, disk size.
'''
import json
from klein import Klein


class InformationApi:
    routes = Klein()

    @routes.route('/hardware')
    def hardware_info(self, request):
        request.setHeader('Content-Type', 'application/json')
        data = dict()
        # TODO: get information from /proc
        data['board'] = 'PC Engine APU1C'
        data['cpu'] = 'AMD G-T40E Processor'
        data['memory'] = '2GB'
        data['disks'] = '64GB'
        return json.dumps(data)

    @routes.route('/software')
    def software_info(self, request):
        request.setHeader('Content-Type', 'application/json')
        data['version'] = '0.3.0'
        return json.dumps(data)
