'''
Core module. Contains the entry point into Paradrop and establishes all other modules.
Does not implement any behavior itself.
'''

import argparse
import signal

from twisted.internet import reactor

from pdtools.lib import output, store, riffle, nexus

from paradrop.lib import settings


class Nexus(nexus.NexusBase):

    def __init__(self):
        ''' Sets up the local paths, loads old config and parses incoming config '''
        super(Nexus, self).__init__('router', devMode=False)

##########################################################################
# Support Functions
##########################################################################


def setupArgParse():
    """
    Sets up arguments if backend is called directly for testing.
    """
    p = argparse.ArgumentParser(description='Paradrop API server running on client')
    p.add_argument('-s', '--settings', help='Overwrite settings, format is "KEY:VALUE"',
                   action='append', type=str, default=[])
    p.add_argument('--development', help='Enable the development environment variables',
                   action='store_true')
    p.add_argument('--config', help='Run as the configuration daemon',
                   action='store_true')
    p.add_argument('--unittest', help="Run the server in unittest mode", action='store_true')
    p.add_argument('--verbose', '-v', help='Enable verbose', action='store_true')

    return p


##########################################################################
# Main Function
##########################################################################

def main():
    # Setup args if called directly (testing)
    p = setupArgParse()
    args = p.parse_args()

    # Check for settings to overwrite (MOVE TO NEXUS)
    settings.updateSettings(args.settings)

    # Globally assign the nexus object so anyone else can access it.
    # Sorry, programming gods. If it makes you feel better this class
    # reduced half a dozen exising singleton implementations
    nexus.core = Nexus()

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
