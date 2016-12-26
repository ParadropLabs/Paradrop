'''
Core module. Contains the entry point into Paradrop and establishes all other modules.
Does not implement any behavior itself.
'''

import argparse
from twisted.internet import reactor

from paradrop.base import output, nexus, settings
from paradrop.backend import apiinternal
from paradrop.backend.update_manager import UpdateManager
from paradrop.backend.http_server import HttpServer, setup_http_server 
from paradrop import confd
from paradrop.lib.misc.procmon import ProcessMonitor

class Nexus(nexus.NexusBase):

    def __init__(self):
        # Want to change logging functionality? See optional args on the base class and pass them here
        super(Nexus, self).__init__(stealStdio=True, printToConsole=True)

    def onStart(self):
        super(Nexus, self).onStart()

        # onStart is called when the reactor starts, not when the connection is made.
        # Check for provisioning keys and attempt to connect
        if not self.provisioned():
            output.out.warn('Router has no keys or identity. Waiting to connect to to server.')
        else:
            return self.connect(apiinternal.RouterSession)

    def onStop(self):
        # if self.session is not None:
        #     self.session.leave()
        # else:
        #     print 'No session found!'

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

    # Globally assign the nexus object so anyone else can access it.
    # Sorry, programming gods. If it makes you feel better this class
    # replaces about half a dozen singletons
    nexus.core = Nexus()

    from paradrop.lib.misc.reporting import sendStateReport
    from paradrop.backend.apibridge import updateManager

    # Start the configuration service as a thread
    confd.main.run_thread(execute=args.execute)

    if nexus.core.provisioned():
        # Set up communication with pdserver.
        # 1. Create a report of the current system state and send that.
        # 2. Poll for a list of updates that should be applied.
        sendStateReport()
        updateManager.startUpdate()

    ProcessMonitor.allowedActions = set()

    update_manager = UpdateManager(reactor)
    http_server = HttpServer(update_manager, args.portal)
    setup_http_server(http_server, '0.0.0.0', settings.PORTAL_SERVER_PORT)

    reactor.run()

if __name__ == "__main__":
    main()
