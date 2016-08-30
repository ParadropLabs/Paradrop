#
# This module collects information about the current state of the system
# (chutes installed, hardware available, etc.) and reports that to the Paradrop
# server for remote management purposes.
#

import json
import time

from StringIO import StringIO

from twisted.internet import reactor
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers

# Sources of system state:
from paradrop.backend.fc import chutestorage
from paradrop.lib.config import devices, hostconfig
from paradrop.lib import settings, status

from paradrop.lib.utils.http import buildAuthString
from pdtools.lib import nexus
from pdtools.lib.output import out


class StateReport(object):
    def __init__(self):
        # Record timestamp when report was created in case the server receives
        # multiple.
        self.timestamp = time.time()

        self.name = None
        self.paradropVersion = None
        self.pdinstallVersion = None
        self.chutes = []
        self.devices = []
        self.hostConfig = {}

    def toJSON(self):
        return json.dumps(self.__dict__)


class StateReportBuilder(object):
    report = StateReport()

    def prepare(self):
        report = StateReport()

        report.name = nexus.core.info.pdid

        # TODO: Get paradrop and pdinstall versions.
        # TODO: Get chute version, time created, etc.

        report.chutes = []
        chuteStore = chutestorage.ChuteStorage()
        for chute in chuteStore.getChuteList():
            report.chutes.append({
                'name': chute.name,
                'state': chute.state,
                'warning': chute.warning,
                'version': None
            })

        report.devices = devices.listSystemDevices()
        report.hostConfig = hostconfig.prepareHostConfig(write=False)

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
        agent = Agent(reactor)

        method = 'POST'
        url = "{}/pdrouters/state".format(settings.PDSERVER_URL)
        headers = Headers({
            'Authorization': [buildAuthString()],
            'Content-Type': ['application/json']
        })
        body = FileBodyProducer(StringIO(report.toJSON()))

        # Check for error code and retry.
        def cbresponse(response):
            if response.code != 200:
                out.warn('{} to {} returned code {}'.format(method, url,
                    response.code))
                reactor.callLater(self.retryDelay, self.send, report)
                self.increaseDelay()
                status.apiTokenVerified = False
            else:
                status.apiTokenVerified = True

        # Check for connection failures and retry.
        def cberror(ignored):
            out.warn('{} to {} failed'.format(method, url))
            reactor.callLater(self.retryDelay, self.send, report)
            self.increaseDelay()
            status.apiTokenVerified = False

        d = agent.request(method, url, headers, body)
        d.addCallback(cbresponse)
        d.addErrback(cberror)


def sendStateReport():
    builder = StateReportBuilder()
    report = builder.prepare()

    sender = ReportSender()
    sender.send(report)
