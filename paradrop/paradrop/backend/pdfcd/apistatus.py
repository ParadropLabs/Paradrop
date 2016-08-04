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

    @APIDecorator()
    def GET_hoststatus(self, apiPkg):
        """
        A method for getting system information
        """
        # initialize cpu, memory, disks
        data = dict()
        data['cpu'] = psutil.cpu_percent(interval=None)
        data['memory'] = psutil.virtual_memory()
        data['disks'] = psutil.disk_partitions()
        result = json.dumps(data)
        apiPkg.request.setHeader('Content-Type', 'application/json')
        apiPkg.setSuccess(result)