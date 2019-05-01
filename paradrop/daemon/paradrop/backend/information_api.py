'''
Provide information of the router, e.g. board version, CPU information,
memory size, disk size.

Endpoints for these functions can be found under /api/v1/info.
'''
import json
import os
import platform
from psutil import virtual_memory
from klein import Klein

from paradrop.base import constants
from paradrop.core.config.devices import detectSystemDevices
from paradrop.core.system.system_info import getOSVersion, getPackageVersion
from paradrop.core.agent.reporting import TelemetryReportBuilder
from paradrop.lib.utils import pdos
from . import cors


class InformationApi(object):
    routes = Klein()

    def __init__(self):
        self.vendor = pdos.read_sys_file('/sys/devices/virtual/dmi/id/sys_vendor')
        self.board = pdos.read_sys_file('/sys/devices/virtual/dmi/id/product_name', default='') \
                     + ' ' + pdos.read_sys_file('/sys/devices/virtual/dmi/id/product_version', default='')
        self.cpu = platform.processor()
        self.memory = virtual_memory().total

        self.wifi = []
        devices = detectSystemDevices()
        for wifiDev in devices['wifi']:
            self.wifi.append({
                'id': wifiDev['id'],
                'macAddr': wifiDev['mac'],
                'vendorId': wifiDev['vendor'],
                'deviceId': wifiDev['device'],
                'slot': wifiDev['slot']
            })

        self.biosVendor = pdos.read_sys_file('/sys/devices/virtual/dmi/id/bios_vendor')
        self.biosVersion = pdos.read_sys_file('/sys/devices/virtual/dmi/id/bios_version')
        self.biosDate = pdos.read_sys_file('/sys/devices/virtual/dmi/id/bios_date')
        self.osVersion = getOSVersion()
        self.kernelVersion = platform.system() + '-' + platform.release()
        self.pdVersion = getPackageVersion('paradrop')
        self.uptime = int(float(pdos.read_sys_file('/proc/uptime', default='0').split()[0]))

    @routes.route('/hardware', methods=['GET'])
    def hardware_info(self, request):
        """
        Get information about the hardware platform.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/info/hardware

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "wifi": [
               {
                 "slot": "pci/0000:04:00.0",
                 "vendorId": "0x168c",
                 "macAddr": "04:f0:21:2f:b7:c1",
                 "id": "pci-wifi-0",
                 "deviceId": "0x003c"
               },
               {
                 "slot": "pci/0000:06:00.0",
                 "vendorId": "0x168c",
                 "macAddr": "04:f0:21:0f:78:28",
                 "id": "pci-wifi-1",
                 "deviceId": "0x002a"
               }
             ],
             "memory": 2065195008,
             "vendor": "PC Engines",
             "board": "APU 1.0",
             "cpu": "x86_64"
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        data = dict()
        data['vendor'] = self.vendor
        data['board'] = self.board
        data['cpu'] = self.cpu
        data['memory'] = self.memory
        data['wifi'] = self.wifi
        return json.dumps(data)

    @routes.route('/software', methods=['GET'])
    def software_info(self, request):
        """
        Get information about the operating system.

        Returns a dictionary containing information the BIOS version, OS
        version, kernel version, Paradrop version, and system uptime.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/info/software

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "biosVersion": "SageBios_PCEngines_APU-45",
             "biosDate": "04/05/2014",
             "uptime": 15351,
             "kernelVersion": "Linux-4.4.0-101-generic",
             "pdVersion": "0.9.2",
             "biosVendor": "coreboot",
             "osVersion": "Ubuntu 4.4.0-101.124-generic 4.4.95"
           }
        """
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

    @routes.route('/environment', methods=['GET'])
    def get_environment(self, request):
        """
        Get environment variables.

        Returns a dictionary containing the environment variables passed to the
        Paradrop daemon.  This is useful for development and debugging purposes
        (e.g. see how PATH is set on Paradrop when running in different
        contexts).

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/info/environment

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "LANG": "C.UTF-8",
             "SNAP_REVISION": "x73",
             "SNAP_COMMON": "/var/snap/paradrop-daemon/common",
             "XDG_RUNTIME_DIR": "/run/user/0/snap.paradrop-daemon",
             "SNAP_USER_COMMON": "/root/snap/paradrop-daemon/common",
             "SNAP_LIBRARY_PATH": "/var/lib/snapd/lib/gl:/var/lib/snapd/void",
             "SNAP_NAME": "paradrop-daemon",
             "PWD": "/var/snap/paradrop-daemon/x73",
             "PATH": "/snap/paradrop-daemon/x73/usr/sbin:/snap/paradrop-daemon/x73/usr/bin:/snap/paradrop-daemon/x73/sbin:/snap/paradrop-daemon/x73/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games",
             "SNAP": "/snap/paradrop-daemon/x73",
             "SNAP_DATA": "/var/snap/paradrop-daemon/x73",
             "SNAP_VERSION": "0.9.2",
             "SNAP_ARCH": "amd64",
             "SNAP_USER_DATA": "/root/snap/paradrop-daemon/x73",
             "TEMPDIR": "/tmp",
             "HOME": "/root/snap/paradrop-daemon/x73",
             "SNAP_REEXEC": "",
             "LD_LIBRARY_PATH": "/var/lib/snapd/lib/gl:/var/lib/snapd/void:/snap/paradrop-daemon/x73/usr/lib/x86_64-linux-gnu::/snap/paradrop-daemon/x73/lib:/snap/paradrop-daemon/x73/usr/lib:/snap/paradrop-daemon/x73/lib/x86_64-linux-gnu:/snap/paradrop-daemon/x73/usr/lib/x86_64-linux-gnu",
             "TMPDIR": "/tmp"
             ...
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(os.environ.data)

    @routes.route('/features', methods=['GET'])
    def get_features(self, request):
        """
        Get features supported by the host.

        This is a list of strings specifying features supported by the daemon.

        **Explanation of feature strings**:

        hostapd-control
          The daemon supports the hostapd control interface and
          provides a websocket channel for accessing it.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/info/features

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             "hostapd-control"
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        features = constants.DAEMON_FEATURES.split()
        return json.dumps(features)

    @routes.route('/telemetry', methods=['GET'])
    def get_telemetry(self, request):
        """
        Get a telemetry report.

        This contains information about resource utilization by chute and
        system totals.  This endpoint returns the same data that we
        periodically send to the controller if telemetry is enabled.
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        builder = TelemetryReportBuilder()
        report = builder.prepare()
        return json.dumps(report)
