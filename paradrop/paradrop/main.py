'''
Core module. Contains the entry point into Paradrop and establishes all other modules.
Does not implement any behavior itself.
'''

import argparse
import signal

from paradrop.lib.utils import output

from paradrop.lib import settings
from paradrop.lib.utils.output import logPrefix
from paradrop.backend import pdfcd


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
    p.add_argument(
        '--unittest', help="Run the server in unittest mode", action='store_true')
    p.add_argument('--verbose', '-v', help='Enable verbose',
                   action='store_true')
    return p


def caughtSIGUSR1(signum, frame):
    """
    Catches SIGUSR1 calls and toggles verbose output
    """
    if(isinstance(PD.out.verbose, PD.FakeOutput)):
        output.out.header("== %s Activating verbose mode\n" % logPrefix())
        output.out.verbose = PD.Stdout(PD.Colors.VERBOSE)
        output.verbose = True
    else:
        output.out.header("== %s Deactivating verbose mode\n" % logPrefix())
        output.verbose = False
        output.out.verbose = PD.FakeOutput()


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

    a = 1 / 0
    # Setup the signal handler for verbose
    signal.signal(signal.SIGUSR1, caughtSIGUSR1)

    # Setup args if called directly (testing)
    p = setupArgParse()
    args = p.parse_args()

    # Check for settings to overwrite
    settings.updateSettings(args.settings)

    if(args.verbose):
        caughtSIGUSR1(signal.SIGUSR1, None)

    # Before we setup anything make sure we have generated a UUID for our instance
    # TODO
    output.out.info('-- {} Testee\n'.format(logPrefix()))

    # Now setup the RESTful API server for Paradrop
    pdfcd.server.setup(args)

if __name__ == "__main__":
    main()
