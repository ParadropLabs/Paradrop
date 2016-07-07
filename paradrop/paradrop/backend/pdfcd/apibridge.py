#
# This module serves as a bridge between the HTTP-based API (chute operations)
# and the WAMP API.
#

from twisted.internet.defer import Deferred

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
