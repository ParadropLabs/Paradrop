import json
import psutil

from pdtools.lib.output import out

from paradrop.lib.api.pdrest import APIDecorator
from paradrop.lib.api import pdapi

class StatusAPI(object):
    """
    Status API.

    This class handles HTTP API calls related to router status.
    """
    def __init__(self, rest):
        self.rest = rest
        self.rest.register('GET', '^/v1/hoststatus', self.GET_hoststatus)
        self.rest.register('GET', '^/v1/netinfo', self.GET_netinfo)

    @APIDecorator()
    def GET_hoststatus(self, apiPkg):
        """
        A method for getting system information
        """
        data = dict()
        data['cpu'] = psutil.cpu_percent(interval=0.2)
        data['memory'] = psutil.virtual_memory()
        data['disks'] = psutil.disk_usage('/')
        data['net'] = psutil.net_io_counters(True)
        result = json.dumps(data)
        apiPkg.request.setHeader('Content-Type', 'application/json')
        apiPkg.setSuccess(result)

    @APIDecorator()
    def GET_netinfo(self, apiPkg):
        data = dict()
        data['interface'] = psutil.net_if_addrs()
        result = json.dumps(data)
        apiPkg.request.setHeader('Content-Type', 'application/json')
        apiPkg.setSuccess(result)
