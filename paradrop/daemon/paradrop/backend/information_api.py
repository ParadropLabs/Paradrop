'''
Provide information of the router, e.g. board version, CPU information,
memory size, disk size.
'''
import json
import platform
from psutil import virtual_memory
from klein import Klein

from paradrop.core.config.devices import detectSystemDevices
from paradrop.core.system.system_info import getOSVersion, getPackageVersion
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

        self.wifi = []
        devices = detectSystemDevices()
        for wifiDev in devices['wifi']:
            self.wifi.append({
                'macAddr': wifiDev['mac'],
                'vendorId': wifiDev['vendor'],
                'deviceId': wifiDev['device'],
                'pciSlot': wifiDev['pci_slot']
            })

        self.biosVendor = pdos.readFile('/sys/devices/virtual/dmi/id/bios_vendor')[0]
        self.biosVersion = pdos.readFile('/sys/devices/virtual/dmi/id/bios_version')[0]
        self.biosDate = pdos.readFile('/sys/devices/virtual/dmi/id/bios_date')[0]
        self.osVersion = getOSVersion()
        self.kernelVersion = platform.system() + '-' + platform.release()
        self.pdVersion = getPackageVersion('paradrop')
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
        data['wifi'] = self.wifi
        return json.dumps(data)

    @routes.route('/software')
    def software_info(self, request):
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        data = dict()
        data['biosVendor'] = self.biosVendor
        data['biosVersion'] = self.biosVersion
        data['biosDate'] = self.biosDate
        data['kernelVersion'] = self.kernelVersion
        data['osVersion'] = self.osVersion
        data['pdVersion'] = self.pdVersion
        data['uptime'] = self.uptime
        return json.dumps(data)
