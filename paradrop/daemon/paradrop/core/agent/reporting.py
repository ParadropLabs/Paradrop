#
# This module collects information about the current state of the system
# (chutes installed, hardware available, etc.) and reports that to the Paradrop
# server for remote management purposes.
#

import json
import os
import time

from twisted.internet import reactor

from paradrop.base.output import out
from paradrop.base import nexus, settings
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.config import devices, hostconfig, resource, zerotier
from paradrop.core.container.chutecontainer import ChuteContainer
from paradrop.core.agent.http import PDServerRequest
from paradrop.core.system import system_info
from paradrop.core.system.system_status import SystemStatus
from paradrop.lib.misc.governor import GovernorClient


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
        self.dmi = {}
        self.status = {}

    def toJSON(self):
        return json.dumps(self.__dict__)


class StateReportBuilder(object):
    def prepare(self):
        report = StateReport()

        report.name = nexus.core.info.pdid

        report.osVersion = system_info.getOSVersion()

        # We can get the paradrop version from the installed python package.
        report.paradropVersion = system_info.getPackageVersion('paradrop')

        report.chutes = []
        chuteStore = ChuteStorage()
        chutes = chuteStore.getChuteList()
        allocation = resource.computeResourceAllocation(chutes)

        for chute in chutes:
            service_info = {}
            for service in chute.get_services():
                container_name = service.get_container_name()
                container = ChuteContainer(container_name)

                service_info[service.name] = {
                    'allocation': allocation.get(container_name, None),
                    'state': container.getStatus()
                }

            # Use the default service (e.g. "main") to report the chute's
            # current state.
            service = chute.get_default_service()
            container = ChuteContainer(service.get_container_name())

            report.chutes.append({
                'name': chute.name,
                'desired': chute.state,
                'state': container.getStatus(),
                'services': service_info,
                'warning': None,
                'version': getattr(chute, 'version', None),
                'allocation': None,  # deprecated
                'environment': getattr(chute, 'environment', None),
                'external': getattr(chute, 'external', None),
                'resources': getattr(chute, 'resources', None)
            })

        report.devices = devices.listSystemDevices()
        report.hostConfig = hostconfig.prepareHostConfig(write=False)

        if GovernorClient.isAvailable():
            client = GovernorClient()
            report.snaps = client.listSnaps()

        report.zerotierAddress = zerotier.getAddress()
        report.dmi = system_info.getDMI()

        # Add CPU, memory, disk, and network interface information.  This gives
        # the controller useful debugging information such as high memory or
        # disk utilization and IP addresses.
        status_source = SystemStatus()
        report.status = status_source.getStatus(max_age=None)

        return report.__dict__


class TelemetryReportBuilder(object):
    def prepare(self):
        chuteStore = ChuteStorage()
        chutes = chuteStore.getChuteList()

        # All network interfaces: we will divide these into chute-specific
        # interfaces and system-wide interfaces.
        network = SystemStatus.getNetworkInfo()
        system_interfaces = set(network.keys())

        report = {
            'chutes': [],
            'network': [],
            'system': SystemStatus.getSystemInfo(),
            'time': time.time()
        }

        for chute in chutes:
            container = ChuteContainer(chute.name)

            chute_info = {
                'name': chute.name,
                'state': container.getStatus(),
                'network': []
            }

            try:
                pid = container.getPID()
                chute_info['process'] = SystemStatus.getProcessInfo(pid)
            except Exception:
                chute_info['process'] = None

            interfaces = chute.getCache('networkInterfaces')
            for iface in interfaces:
                ifname = iface['externalIntf']
                if ifname in network:
                    ifinfo = network[ifname]
                    ifinfo['name'] = ifname
                    ifinfo['type'] = iface.get('type', 'wifi')
                    chute_info['network'].append(ifinfo)
                    system_interfaces.remove(ifname)

            report['chutes'].append(chute_info)

        for ifname in system_interfaces:
            ifinfo = network[ifname]
            ifinfo['name'] = ifname
            ifinfo['type'] = None
            report['network'].append(ifinfo)

        return report


class ReportSender(object):
    def __init__(self, model="states", max_retries=None):
        self.max_retries = max_retries
        self.model = model
        self.retries = 0
        self.retryDelay = 1
        self.maxRetryDelay = 300

    def increaseDelay(self):
        self.retryDelay *= 2
        if self.retryDelay > self.maxRetryDelay:
            self.retryDelay = self.maxRetryDelay

    def send(self, report):
        request = PDServerRequest('/api/routers/{router_id}/' + self.model)
        d = request.post(**report)

        # Check for error code and retry.
        def cbresponse(response):
            if not response.success:
                out.warn('{} to {} returned code {}'.format(request.method,
                    request.url, response.code))
                if self.max_retries is None or self.retries < self.max_retries:
                    reactor.callLater(self.retryDelay, self.send, report)
                    self.retries += 1
                    self.increaseDelay()
                nexus.core.jwt_valid = False
            else:
                nexus.core.jwt_valid = True

        # Check for connection failures and retry.
        def cberror(ignored):
            out.warn('{} to {} failed'.format(request.method, request.url))
            if self.max_retries is None or self.retries < self.max_retries:
                reactor.callLater(self.retryDelay, self.send, report)
                self.retries += 1
                self.increaseDelay()
            nexus.core.jwt_valid = False

        d.addCallback(cbresponse)
        d.addErrback(cberror)
        return d


class NodeIdentitySender(ReportSender):
    def send(self, report):
        request = PDServerRequest('/api/routers/{router_id}')
        d = request.patch(*report)

        # Check for error code and retry.
        def cbresponse(response):
            if not response.success:
                out.warn('{} to {} returned code {}'.format(request.method,
                    request.url, response.code))
                if self.max_retries is None or self.retries < self.max_retries:
                    reactor.callLater(self.retryDelay, self.send, report)
                    self.retries += 1
                    self.increaseDelay()
                nexus.core.jwt_valid = False
            else:
                nexus.core.jwt_valid = True

        # Check for connection failures and retry.
        def cberror(ignored):
            out.warn('{} to {} failed'.format(request.method, request.url))
            if self.max_retries is None or self.retries < self.max_retries:
                reactor.callLater(self.retryDelay, self.send, report)
                self.retries += 1
                self.increaseDelay()
            nexus.core.jwt_valid = False

        d.addCallback(cbresponse)
        d.addErrback(cberror)
        return d


def sendNodeIdentity():
    path = os.path.join(settings.KEY_DIR, "node.pub")
    with open(path, "r") as source:
        public_key = source.read().strip()

    report = [
        {"op": "add", "path": "/ssh_public_key", "value": public_key}
    ]
    sender = NodeIdentitySender()
    return sender.send(report)


def sendStateReport():
    builder = StateReportBuilder()
    report = builder.prepare()

    sender = ReportSender()
    return sender.send(report)


def sendTelemetryReport():
    # Do not try to send telemetry report if not provisioned.
    if not nexus.core.provisioned():
        if not getattr(sendTelemetryReport, 'provisionWarningShown', False):
            out.warn("Unable to send telemetry report: not provisioned")
            sendTelemetryReport.provisionWarningShown = True
        return None

    builder = TelemetryReportBuilder()
    report = builder.prepare()

    sender = ReportSender(model="telemetry", max_retries=0)
    return sender.send(report)
