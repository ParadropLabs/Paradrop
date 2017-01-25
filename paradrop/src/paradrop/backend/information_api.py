'''
Provide information of the router, e.g. board version, CPU information,
memory size, disk size.
'''
import json
import platform
from psutil import virtual_memory
from klein import Klein


from paradrop.core.agent import reporting
from paradrop.lib.utils import pdos
from . import cors

class InformationApi:
    routes = Klein()

    def __init__(self):
        self.vendor = pdos.readFile('/sys/devices/virtual/dmi/id/sys_vendor')[0]
        self.board = pdos.readFile('/sys/devices/virtual/dmi/id/product_name')[0] \
                     + ' ' + pdos.readFile('/sys/devices/virtual/dmi/id/product_version')[0]
        self.cpu = platform.processor()
        self.memory = virtual_memory().total

        self.biosVendor = pdos.readFile('/sys/devices/virtual/dmi/id/bios_vendor')[0]
        self.biosVersion = pdos.readFile('/sys/devices/virtual/dmi/id/bios_version')[0]
        self.biosDate = pdos.readFile('/sys/devices/virtual/dmi/id/bios_date')[0]
        self.osVersion = platform.platform()
        self.kernelVersion = platform.system() + '-' + platform.release()
        self.uptime = int(float(pdos.readFile('/proc/uptime')[0].split()[0]))

    @routes.route('/hardware')
    def hardware_info(self, request):
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        data = dict()
        data['vendor'] = self.vendor 
        data['board'] = self.board
        data['cpu'] = self.cpu
        data['memory'] = self.memory
        return json.dumps(data)

    @routes.route('/software')
    def software_info(self, request):
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        data = dict()
        data['pdVersion'] = reporting.getPackageVersion('paradrop')
        data['biosVendor'] = self.biosVendor
        data['biosVersion'] = self.biosVersion
        data['biosDate'] = self.biosDate
        data['osVersion'] = self.osVersion
        data['kernelVersion'] = self.kernelVersion
        data['uptime'] = self.uptime
        return json.dumps(data)
