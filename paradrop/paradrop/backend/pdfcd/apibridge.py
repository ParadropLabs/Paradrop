#
# This module serves as a bridge between the HTTP-based API (chute operations)
# and the WAMP API.
#
import json

from StringIO import StringIO

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers

from paradrop.lib.utils.http import JSONReceiver
from pdtools.lib import nexus
from pdtools.lib.pdutils import timeint


class BridgeRequest(object):
    """
    This class mimics the request object used by the HTTP API code.  It has two
    required methods, write and finish.
    """
    def write(self, s):
        print(s)

    def finish(self):
        print("finish")


class BridgePackage(object):
    """
    This class mimics the apipkg variable that the HTTP API code uses.  It has
    a request object with certain methods that the code requires to be defined.
    """
    def __init__(self):
        self.request = BridgeRequest()


class UpdateCallback(object):
    def __init__(self, d):
        self.d = d

    def __call__(self, update):
        # Call the deferred callback function with just the result (a
        # dictionary containing success and message fields).
        return self.d.callback(update.result)


class APIBridge(object):
    configurer = None

    @classmethod
    def setConfigurer(cls, configurer):
        """
        Set the chute configurer (instance of PDConfigurer).

        The configurer is expected to be a singleton, so this should be called
        once when the configurer is created.
        """
        cls.configurer = configurer

    def updateChute(self, updateType, **options):
        """
        Initiate a chute operation.

        For delete, start, and stop operations, options must include a 'name'
        field.

        updateType: must be a string, one of ['create', 'delete', 'start', 'stop']

        Returns a Deferred object that will be resolved when the operation has
        been completed.
        """
        if APIBridge.configurer is None:
            raise Exception("Error: chute configurer is not available.")

        d = Deferred()

        update = dict(updateClass='CHUTE',
                updateType=updateType,
                tok=timeint(),
                pkg=BridgePackage(),
                func=UpdateCallback(d))
        update.update(**options)
        APIBridge.configurer.updateList(**update)

        return d

    def createChute(self, config):
        return self.updateChute('create', **config)

    def deleteChute(self, name):
        return self.updateChute('delete', name=name)

    def startChute(self, name):
        return self.updateChute('start', name=name)

    def stopChute(self, name):
        return self.updateChute('stop', name=name)


class UpdateManager(object):
    def __init__(self):
        # Store set of update IDs that are in progress in order to avoid
        # repeats.
        self.updatesInProgress = set()

    def startUpdate(self):
        """
        Start updates by polling the server for the latest updates.

        This is the only method that needs to be called from outside.  The rest
        are triggered asynchronously.

        Call chain:
        startUpdate -> queryOpened -> updatesReceived -> updateComplete
        """
        agent = Agent(reactor)

        method = 'GET'
        url = "{}/pdserver/updates/?router={}&completed=false".format(
                nexus.core.net.webHost, nexus.core.info.pdid)
        headers = Headers({
            # TODO: Authorization
        })

        d = agent.request(method, url, headers, None)
        d.addCallback(self.queryOpened)

    def queryOpened(self, response):
        """
        Internal: callback after GET request has been opened and set up for
        receiving the list of updates.
        """
        finished = Deferred()
        response.deliverBody(JSONReceiver(finished))
        finished.addCallback(self.updatesReceived)

    def updatesReceived(self, updates):
        """
        Internal: callback after list of updates has been received.
        """
        print("Received {} update(s) from server.".format(len(updates)))
        for item in updates:
            if item['_id'] in self.updatesInProgress:
                continue
            else:
                self.updatesInProgress.add(item['_id'])

            update = dict(updateClass=item['updateClass'],
                    updateType=item['updateType'],
                    tok=timeint(),
                    pkg=BridgePackage(),
                    func=self.updateComplete)
            update['_id'] = item['_id']
            update.update(item['config'])
            APIBridge.configurer.updateList(**update)

    def updateComplete(self, update):
        """
        Internal: callback after an update operation has been completed
        (successfuly or otherwise) and send a notification to the server.
        """
        agent = Agent(reactor)

        changes = {
            'completed': True,
            'result': update.result
        }
        data = json.dumps(changes)

        method = 'PUT'
        url = "{}/pdserver/updates/{}".format(
                nexus.core.net.webHost, update._id)
        headers = Headers({
            # TODO: Authorization
            'Content-Type': ['application/json']
        })
        body = FileBodyProducer(StringIO(data))

        def serverNotified():
            if update._id in self.updatesInProgress:
                self.updatesInProgress.remove(update._id)

        # TODO: If this notification fails to go through, we should retry or
        # build in some other mechanism to inform the server.
        d = agent.request(method, url, headers, body)
        d.addCallback(serverNotified)


updateManager = UpdateManager()
