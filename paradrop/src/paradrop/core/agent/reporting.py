#
# This module collects information about the current state of the system
# (chutes installed, hardware available, etc.) and reports that to the Paradrop
# server for remote management purposes.
#

import json
import pkg_resources
import time

from StringIO import StringIO

from twisted.internet import reactor
from twisted.web.http_headers import Headers

from paradrop.base import nexus, settings
from paradrop.base.output import out
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.config import devices, hostconfig, resource, zerotier
from paradrop.core.container.chutecontainer import ChuteContainer
from paradrop.core.agent.http import PDServerRequest
from paradrop.lib.misc.snapd import SnapdClient


def getOSVersion():
    """
    Return a string identifying the host OS.
    """
    try:
        with open('/proc/version_signature', 'r') as source:
            return source.read().strip()
    except:
        return None


def getPackageVersion(name):
    """
    Get a python package version.

    Returns: a string or None
    """
    try:
        pkg = pkg_resources.get_distribution(name)
        return pkg.version
    except:
        return None


class StateReport(object):
    def __init__(self):
        # Record timestamp when report was created in case the server receives
        # multiple.
        self.timestamp = time.time()

        self.name = None
        self.osVersion = None
        self.paradropVersion = None
        self.pdinstallVersion = None
        self.chutes = []
        self.devices = []
        self.hostConfig = {}
        self.snaps = []
        self.zerotierAddress = None

    def toJSON(self):
        return json.dumps(self.__dict__)


class StateReportBuilder(object):
    report = StateReport()

    def prepare(self):
        report = StateReport()

        report.name = nexus.core.info.pdid

        report.osVersion = getOSVersion()

        # We can get the paradrop version from the installed python package.
        report.paradropVersion = getPackageVersion('paradrop')

        # TODO: Get pdinstall version - we will have to work with snappy or
        # devise some other mechanism, since it installs as a completely
        # separate snap.

        report.chutes = []
        chuteStore = ChuteStorage()
        chutes = chuteStore.getChuteList()
        allocation = resource.computeResourceAllocation(chutes)

        for chute in chutes:
            container = ChuteContainer(chute.name)

            report.chutes.append({
                'name': chute.name,
                'desired': chute.state,
                'state': container.getStatus(),
                'warning': chute.warning,
                'version': getattr(chute, 'version', None),
                'allocation': allocation.get(chute.name, None),
                'environment': getattr(chute, 'environment', None),
                'external': getattr(chute, 'external', None),
                'resources': getattr(chute, 'resources', None)
            })

        report.devices = devices.listSystemDevices()
        report.hostConfig = hostconfig.prepareHostConfig(write=False)

        client = SnapdClient()
        report.snaps = client.listSnaps()

        report.zerotierAddress = zerotier.getAddress()

        return report


class ReportSender(object):
    def __init__(self):
        self.retryDelay = 1
        self.maxRetryDelay = 300

    def increaseDelay(self):
        self.retryDelay *= 2
        if self.retryDelay > self.maxRetryDelay:
            self.retryDelay = self.maxRetryDelay

    def send(self, report):
        request = PDServerRequest('/api/routers/{router_id}/states')
        d = request.post(**report.__dict__)

        # Check for error code and retry.
        def cbresponse(response):
            if not response.success:
                out.warn('{} to {} returned code {}'.format(request.method,
                    request.url, response.code))
                reactor.callLater(self.retryDelay, self.send, report)
                self.increaseDelay()
                nexus.core.jwt_valid = False
            else:
                nexus.core.jwt_valid = True

        # Check for connection failures and retry.
        def cberror(ignored):
            out.warn('{} to {} failed'.format(request.method, request.url))
            reactor.callLater(self.retryDelay, self.send, report)
            self.increaseDelay()
            nexus.core.jwt_valid = False

        d.addCallback(cbresponse)
        d.addErrback(cberror)
        return d


def sendStateReport():
    builder = StateReportBuilder()
    report = builder.prepare()

    sender = ReportSender()
    return sender.send(report)
