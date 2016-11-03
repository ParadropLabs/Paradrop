import json
import smokesignal

from twisted.web import xmlrpc
from twisted.internet import utils
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from autobahn.wamp import auth

from paradrop.lib import pdinstall, status
from paradrop.lib.config import hostconfig
from pdtools.lib.output import out
from pdtools.lib import names, nexus, cxbr

from . import apibridge


class RouterSession(cxbr.BaseSession):

    def __init__(self, *args, **kwargs):
        self.bridge = apibridge.APIBridge()
        self.uriPrefix = 'org.paradrop.'
        super(RouterSession, self).__init__(*args, **kwargs)

    def onConnect(self):
        out.info('Router session connected.')
        if (nexus.core.info.pdid and nexus.core.getKey('apitoken')):
            out.info('Starting WAMP-CRA authentication on realm "{}" as user "{}"...'\
                     .format(self.config.realm, nexus.core.info.pdid))
            self.join(self.config.realm, [u'wampcra'], nexus.core.info.pdid)

    def onChallenge(self, challenge):
        if challenge.method == u"wampcra":
            out.verbose("WAMP-CRA challenge received: {}".format(challenge))

            wampPassword = nexus.core.getKey('apitoken')
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

        status.wampConnected = True

        # TEMP: ping the server, let it know we just came up
        # yield self.call('pd', 'routerConnected', self._session_id)
        yield self.subscribe(self.updatesPending, self.uriPrefix + 'updatesPending')
        yield self.register(self.ping, self.uriPrefix + 'ping')
        yield self.register(self.update, self.uriPrefix + 'update')
        # yield self.register(self.logsFromTime, 'logsFromTime')
        yield self.register(self.getConfig, self.uriPrefix + 'getConfig')
        yield self.register(self.setConfig, self.uriPrefix + 'setConfig')

        yield self.register(self.createChute, self.uriPrefix + 'createChute')
        yield self.register(self.updateChute, self.uriPrefix + 'updateChute')
        yield self.register(self.deleteChute, self.uriPrefix + 'deleteChute')
        yield self.register(self.startChute, self.uriPrefix + 'startChute')
        yield self.register(self.stopChute, self.uriPrefix + 'stopChute')

        # route output to the logs call
        smokesignal.on('logs', self.logs)

        yield cxbr.BaseSession.onJoin(self, details)

    def onLeave(self, details):
        out.info("Router session left: {}".format(details))
        status.wampConnected = False
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

    def updateChute(self, pdid, config):
        out.info('Updating chute...')
        return self.bridge.updateChute(config)

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
