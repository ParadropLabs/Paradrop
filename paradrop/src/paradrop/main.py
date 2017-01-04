'''
Core module.
Contains the entry point into Paradrop and establishes all other modules.
Does not implement any behavior itself.
'''

import argparse
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from paradrop.base.output import out
from paradrop.base import nexus, settings
from paradrop.lib.misc.procmon import ProcessMonitor
from paradrop.lib.misc.reporting import sendStateReport
from paradrop.backend.update_fetcher import UpdateFetcher
from paradrop.backend.update_manager import UpdateManager
from paradrop.backend.http_server import HttpServer, setup_http_server
from paradrop.backend.wamp_session import WampSession
from paradrop import confd


class Nexus(nexus.NexusBase):
    def __init__(self, update_fetcher):
        self.update_fetcher = update_fetcher
        # Want to change logging functionality? See optional args on the base class and pass them here
        super(Nexus, self).__init__(stealStdio=True, printToConsole=True)


    @inlineCallbacks
    def onStart(self):
        super(Nexus, self).onStart()
        # onStart is called when the reactor starts, not when the connection is made.
        # Check for provisioning keys and attempt to connect
        if not self.provisioned():
            out.warn('Router has no keys or identity. Waiting to connect to to server.')
        else:
            # Try to connect to the WAMP router (crossbar.io)
            try:
                wamp_session = yield self.connect(WampSession)
            except Exception:
                out.warn('The router ID or password is invalid!')
            else:
                wamp_session.set_update_fetcher(self.update_fetcher)
                # Set up communication with pdserver.
                # 1. Create a report of the current system state and send that.
                # 2. Poll for a list of updates that should be applied.
                sendStateReport()
                self.update_fetcher.start_polling()


    def onStop(self):
        if self.session is not None:
            self.session.leave()
        else:
            out.info('No WAMP session found!')

        super(Nexus, self).onStop()


def main():
    p = argparse.ArgumentParser(description='Paradrop daemon running on client')
    p.add_argument('--mode', '-m', help='Set the mode to one of [production, local, unittest]',
                   action='store', type=str, default='production')
    p.add_argument('--portal', '-p', help='Set the folder of files for local portal',
                   action='store', type=str)
    p.add_argument('--no-exec', help='Skip execution of configuration commands',
                   action='store_false', dest='execute')

    p.add_argument('--verbose', '-v', help='Enable verbose', action='store_true')

    args = p.parse_args()
    # print args

    settings.loadSettings(args.mode, [])

    update_manager = UpdateManager(reactor)
    update_fetcher = UpdateFetcher(update_manager)
    ProcessMonitor.allowedActions = set()

    # Start the configuration service as a thread
    confd.main.run_thread(execute=args.execute)

    # Globally assign the nexus object so anyone else can access it.
    nexus.core = Nexus(update_fetcher)
    http_server = HttpServer(update_manager, update_fetcher, args.portal)
    setup_http_server(http_server, '0.0.0.0', settings.PORTAL_SERVER_PORT)

    reactor.run()


if __name__ == "__main__":
    main()
