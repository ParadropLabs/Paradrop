'''
The WAMP session of the paradrop daemon
'''

import smokesignal

from twisted.internet.defer import inlineCallbacks
from autobahn.wamp import auth

from paradrop.lib.misc import pdinstall
from paradrop.base.output import out
from paradrop.base import nexus
from paradrop.base.cxbr import BaseSession


class WampSession(BaseSession):
    def __init__(self, *args, **kwargs):
        self.uriPrefix = 'org.paradrop.'
        self.update_fetcher = None
        super(WampSession, self).__init__(*args, **kwargs)

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

        yield self.subscribe(self.updatesPending, self.uriPrefix + 'updatesPending')
        yield self.register(self.update, self.uriPrefix + 'update')

        # route output to the logs call
        smokesignal.on('logs', self.logs)

        yield BaseSession.onJoin(self, details)


    def onLeave(self, details):
        out.info("Router session left: {}".format(details))
        nexus.core.wamp_connected = False
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


    def update(self, pdid, data):
        print("Sending command {} to pdinstall".format(data['command']))
        success = pdinstall.sendCommand(data['command'], data)

        # NOTE: If successful, this process will probably be going down soon.
        if success:
            return "Sent command to pdinstall"
        else:
            return "Sending command to pdinstall failed"


    def set_update_fetcher(self, update_fetcher):
        self.update_fetcher = update_fetcher


    @inlineCallbacks
    def updatesPending(self, pdid):
        out.info('Notified of updates...')
        if self.update_fetcher is not None:
            out.info('Pulling updates from the server...')
            yield self.update_fetcher.pull_update()
