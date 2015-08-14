'''
Core module. Contains the entry point into Paradrop and establishes all other modules.
Does not implement any behavior itself.
'''

import argparse
import signal

import smokesignal
from twisted.internet import reactor, defer

from pdtools.lib import output, store, riffle, nexus, names
from paradrop.lib import settings
from paradrop.backend.pdfcd import apiinternal


class Nexus(nexus.NexusBase):

    def __init__(self, mode):
        # Want to change logging functionality? See optional args on the base class and pass them here
        super(Nexus, self).__init__('router', stealStdio=True, mode=mode)

    def onStart(self):
        super(Nexus, self).onStart()

        # register for new server connections
        smokesignal.on('ServerPerspectiveConnected', self.serverConnected)
        smokesignal.on('ServerPerspectiveDisconnected', self.serverConnected)

        # Create riffle realms
        riffle.portal.addRealm(names.matchers[names.NameTypes.server], riffle.Realm(apiinternal.ServerPerspective))
        riffle.portal.addRealm(names.matchers[names.NameTypes.user], riffle.Realm(apiinternal.ToolsPerspective))

        if not self.provisioned():
            output.out.warn('Router has no keys or identity. Waiting to connect to to server.')
        else:
            reactor.callLater(.1, self.connect)

    def onStop(self):
        super(Nexus, self).onStop()

    def serverConnected(self, avatar, realm):
        output.out.info('Server Connected!')

    def serverDisconnected(self, avatar, realm):
        output.out.warn('Server Disconnected!')
        reactor.callLater(.1, self.connect)

    @defer.inlineCallbacks
    def connect(self):
        ''' Continuously tries to connect to server '''
        print 'Trying to connect to server...'

        try:
            yield riffle.portal.connect()
        except:
            reactor.callLater(3, self.connect)
            defer.returnValue(True)


def main():
    p = argparse.ArgumentParser(description='Paradrop API server running on client')
    p.add_argument('-s', '--settings', help='Overwrite settings, format is "KEY:VALUE"',
                   action='append', type=str, default=[])
    p.add_argument('--development', help='Enable the development environment variables',
                   action='store_true')
    p.add_argument('--config', help='Run as the configuration daemon',
                   action='store_true')
    p.add_argument('--unittest', help="Run the server in unittest mode", action='store_true')
    p.add_argument('--verbose', '-v', help='Enable verbose', action='store_true')
    p.add_argument('--mode', '-m', help='Set the mode to one of [development, production, test, local]',
                   action='store', type=str, default='production')

    # Temporary until the mode=local is hooked up
    p.add_argument('--local', '-l', help='Run on local machine', action='store_true')

    args = p.parse_args()

    # Temp- this should go to nexus (the settings portion of it, at least)
    # Change the confd directories so we can run locally
    if args.local:
        settings.PDCONFD_WRITE_DIR = "/tmp/pdconfd"
        settings.UCI_CONFIG_DIR = "/tmp/config"

    # Check for settings to overwrite (MOVE TO NEXUS)
    settings.updateSettings(args.settings)

    # Globally assign the nexus object so anyone else can access it.
    # Sorry, programming gods. If it makes you feel better this class
    # replaces about half a dozen singletons
    nexus.core = Nexus(mode=args.mode)

    if args.config:
        from paradrop.backend import pdconfd

        # Start the configuration daemon
        pdconfd.main.run_pdconfd()

    else:
        from paradrop.backend import pdconfd
        from paradrop.backend import pdfcd

        # Start the configuration service as a thread
        pdconfd.main.run_thread()

        # Now setup the RESTful API server for Paradrop
        pdfcd.server.setup(args)


if __name__ == "__main__":
    main()
