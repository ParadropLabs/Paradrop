'''
Core module. Contains the entry point into Paradrop and establishes all other modules.
Does not implement any behavior itself.
'''

import argparse
import signal

from pdtools.lib import output, store
from paradrop.lib import settings

from twisted.internet import reactor


##########################################################################
# Support Functions
##########################################################################
def setupArgParse():
    """
    Sets up arguments if backend is called directly for testing.
    """
    p = argparse.ArgumentParser(
        description='Paradrop API server running on client')
    p.add_argument('-s', '--settings', help='Overwrite settings, format is "KEY:VALUE"',
                   action='append', type=str, default=[])
    p.add_argument('--development', help='Enable the development environment variables',
                   action='store_true')
    p.add_argument('--config', help='Run as the configuration daemon',
                   action='store_true')
    p.add_argument(
        '--unittest', help="Run the server in unittest mode", action='store_true')
    p.add_argument('--verbose', '-v', help='Enable verbose',
                   action='store_true')
    return p


def caughtSIGUSR1(signum, frame):
    """
    Catches SIGUSR1 calls and toggles verbose output
    """
    if(isinstance(output.out.verbose, output.FakeOutput)):
        output.out.header("Activating verbose mode\n")
        output.out.verbose = output.Stdout(output.Colors.VERBOSE)
        output.verbose = True
    else:
        output.out.header("Deactivating verbose mode\n")
        output.verbose = False
        output.out.verbose = output.FakeOutput()


def onShutdown():
    ''' Get notified of system shutdown from Twisted '''

    # Clears the print buffer, closes the logfile
    output.out.endFileLogging()

    # TODO: inform the server

    # TODO: inform pdconfd


##########################################################################
# Main Function
##########################################################################

def main():
    """
    This function does something. Right now what its doing is demonstrating
    a docstring with sphinxy additions.

    :param name: The name to use.
    :type name: str.
    :param state: Current state to be in.
    :type state: bool.
    :returns: int -- the return code.
    :raises: AttributeError, KeyError
    """

    # Setup the signal handler for verbose
    signal.signal(signal.SIGUSR1, caughtSIGUSR1)

    # Setup args if called directly (testing)
    p = setupArgParse()
    args = p.parse_args()

    # Check for settings to overwrite
    settings.updateSettings(args.settings)

    if(args.verbose or settings.VERBOSE):
        caughtSIGUSR1(signal.SIGUSR1, None)

    # Ask the shared store to setup (paths can be set up there)
    store.configureLocalPaths()
    store.store = store.Storage()

    # Inform output it should being logging to file
    output.out.startLogging(filePath=store.LOG_PATH, stealStdio=False, printToConsole=True)

    # Register for the shutdown callback so we can gracefully close logging
    reactor.addSystemEventTrigger('before', 'shutdown', onShutdown)

    if args.config:
        from paradrop.backend import pdconfd

        # Start the configuration daemon
        pdconfd.main.run_pdconfd()

    else:
        from paradrop.backend import pdfcd

        # Now setup the RESTful API server for Paradrop
        pdfcd.server.setup(args)

if __name__ == "__main__":
    main()
