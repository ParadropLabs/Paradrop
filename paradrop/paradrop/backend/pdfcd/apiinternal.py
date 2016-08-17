import json
import smokesignal

from twisted.web import xmlrpc
from twisted.internet import utils
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from autobahn.wamp import auth

from paradrop.lib import pdinstall
from paradrop.lib.config import hostconfig
from pdtools.lib.output import out
from pdtools.lib import names, nexus, cxbr

from . import apibridge


class RouterSession(cxbr.BaseSession):

    def __init__(self, *args, **kwargs):
        self.bridge = apibridge.APIBridge()

        super(RouterSession, self).__init__(*args, **kwargs)

    def onConnect(self):
        out.info('Router session connected.')
        if (nexus.core.info.pdid and nexus.core.getKey('wamppassword')):
            out.info('Starting WAMP-CRA authentication on realm "{}" as user "{}"...'\
                     .format(self.config.realm, nexus.core.info.pdid))
            self.join(self.config.realm, [u'wampcra'], nexus.core.info.pdid)

    def onChallenge(self, challenge):
        if challenge.method == u"wampcra":
            out.verbose("WAMP-CRA challenge received: {}".format(challenge))

            wampPassword = nexus.core.getKey('wamppassword')
            if u'salt' in challenge.extra:
                # salted secret
                key = auth.derive_key(wampPassword,
                                      challenge.extra['salt'],
                                      challenge.extra['iterations'],
                                      challenge.extra['keylen'])
            else:
                # plain, unsalted secret
                key = wampPassword

            # compute signature for challenge, using the key
            signature = auth.compute_wcs(key, challenge.extra['challenge'])

            # return the signature to the router for verification
            return signature

        else:
            raise Exception("Invalid authmethod {}".format(challenge.method))

    @inlineCallbacks
    def onJoin(self, details):
        out.info('Router session joined')
        # TEMP: ping the server, let it know we just came up
        # yield self.call('pd', 'routerConnected', self._session_id)

        yield self.subscribe(self.updatesPending, 'updatesPending')

        yield self.register(self.ping, 'ping')
        yield self.register(self.update, 'update')
        # yield self.register(self.logsFromTime, 'logsFromTime')
        yield self.register(self.getConfig, 'getConfig')
        yield self.register(self.setConfig, 'setConfig')

        yield self.register(self.createChute, 'createChute')
        yield self.register(self.deleteChute, 'deleteChute')
        yield self.register(self.startChute, 'startChute')
        yield self.register(self.stopChute, 'stopChute')

        # route output to the logs call
        smokesignal.on('logs', self.logs)

        yield cxbr.BaseSession.onJoin(self, details)

    def onLeave(self, details):
        out.info("Router session left: {}".format(details))
        self.disconnect()

    def onDisconnect(self):
        out.info("Router session disconnected.")

    @inlineCallbacks
    def logs(self, logs):
        ''' Called by the paradrop system when new logs come in '''

        # If ANYTHING throws an exception here you enter recursive hell,
        # since printing an exception will flood this method. No way out,
        # have to throw the logs away
        try:
            # Temp fix- these will eventually be batched as a list, but not yet
            logs = [logs]

            # Naive implementation: step 1- send logs to server
            yield self.call('pd', 'saveLogs', logs)

            # Step 2- broadcast our logs under our pdid
            yield self.publish(self.pdid, 'logs', logs)
        except:
            yield

    def logsFromTime(self, start):
        '''
        Loads logs that have timestamps after the given time. 

        :param start: seconds since epoch from which to start returning logs
        :type start: int.
        :returns: list of logs
        '''

        return out.getLogsSince(start, purge=False)

    # Does not allow the shutdown call to go out before the system goes down
    # @inlineCallbacks
    # def onClose(self, a):
    #     print 'Asked to close!'
    #     yield self.call('pd._disconnected', self.pdid)

    # @inlineCallbacks
    # def onLeave(self, details):
    #     print 'On Leave'
    # yield self.call('pd._disconnected', self.pdid)
    #     cxbr.BaseSession.onLeave(self, details)

    # def onDisconnect(self):
    #     out.info("Crossbar session detaching")

    # self.call('pd._disconnected', self.pdid)
    #     smokesignal.disconnect(self.logs)

    def ping(self, pdid):
        print 'Router ping'
        return 'Router ping receipt'

    def update(self, pdid, data):
        print("Sending command {} to pdinstall".format(data['command']))
        success = pdinstall.sendCommand(data['command'], data)

        # NOTE: If successful, this process will probably be going down soon.
        if success:
            return "Sent command to pdinstall"
        else:
            return "Sending command to pdinstall failed"

    def getConfig(self, pdid):
        config = hostconfig.prepareHostConfig()
        result = json.dumps(config, separators=(',',':'))
        return result

    def setConfig(self, pdid, config):
        config = json.loads(config)
        return self.bridge.updateHostConfig(config)

    def createChute(self, pdid, config):
        out.info('Creating chute...')
        return self.bridge.createChute(config)

    def deleteChute(self, pdid, name):
        out.info('Deleting chute...')
        return self.bridge.deleteChute(name)

    def startChute(self, pdid, name):
        out.info('Starting chute...')
        return self.bridge.startChute(name)

    def stopChute(self, pdid, name):
        out.info('Stopping chute...')
        return self.bridge.stopChute(name)

    def updatesPending(self, pdid):
        out.info('Notified of updates...')
        apibridge.updateManager.startUpdate()


###############################################################################
# Old
###############################################################################


@inlineCallbacks
def api_provision(pdid, key, cert):
    '''
    Provision this router with an id and a set of keys. 

    This is a temporary call until the provisioning process is finalized.
    '''
    # temp: check to make sure we're not already provisioned. Do not allow for
    # multiple provisioning. This is a little hacky-- better to move this into store
    # if nexus.core.provisioned():
    #     raise ValueError("This device is already provisioned as " + nexus.core.info.pdid)

    # nexus.core.set('pdid', pdid)
    nexus.core.provision(pdid, None)

    nexus.core.saveKey(key, 'pub')
    nexus.core.saveKey(cert, 'ca')

    # Attempt to connect. WARNING- what happens if we're already connected?
    # Or if we timeout on the connection? The caller will never receive a response
    yield nexus.core.connect(RouterSession)

    # Return success to the user
    returnValue('Done!')

###############################################################################
# Temporary-- this needs a home, haven't decided where yet.
###############################################################################


class Base(xmlrpc.XMLRPC):

    def __init__(self, module, **kwargs):
        xmlrpc.XMLRPC.__init__(self, kwargs)

        # build a dict of exposed api methods
        self.apiFunctions = {k.replace('api_', ''): apiWrapper(getattr(module, k)) for k in dir(module) if 'api_' in k}

    def lookupProcedure(self, procedurePath):
        try:
            return self.apiFunctions[procedurePath]
        except KeyError:
            raise xmlrpc.NoSuchFunction(self.NOT_FOUND, "procedure %s not found" % procedurePath)


def castFailure(failure):
    ''' Converts an exception (or general failure) into an xmlrpc fault for transmission. '''
    out.info("Failed API call (TODO: categorize errors)")

    raise xmlrpc.Fault(123, failure.getErrorMessage())


def apiWrapper(target):
    ''' Add a final line of error and success callbacks before going onto the wire'''

    def outside(*args):
        return target(*args).addErrback(castFailure).addCallback(castSuccess)

    return outside


def castSuccess(res):
    out.info("Completed API call (TODO: add details)")

    # screen out Objectids on mongo returns. The remote objects have no
    # need for them, and they confuse xmlrpc
    if isinstance(res, dict):
        res.pop('_id', None)

    return res
