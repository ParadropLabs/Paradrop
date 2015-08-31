'''
Entry point for client tools.

This module has two logical sections: extracting and validating arguments, and 
sending program flow into the correct function.

Structurally there are three sections. In order:
    - Literal docstrings users see
    - Subcommand handlers
    - Entry point

The main method calls docopt, which parses the first positional command given.
If that command matches a sub-command the correct handler is invoked. 

Docopt will not allow execution to continue if the args matcher fails (in other words:
dont worry about failure conditions.) Check documentation for more information.

To run this code from the command line:
    export PDCONFD_WRITE_DIR="/tmp/pdconfd"
    export UCI_CONFIG_DIR="/tmp/config"
'''

from pkg_resources import get_distribution
import sys

from docopt import docopt
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from pdtools.lib import output, riffle, names, cxbr, nexus
from pdtools.coms import routers, general, server
from pdtools.lib.store import store

# SERVER_HOST = 'paradrop.io'
SERVER_HOST = 'localhost'
SERVER_PORT = 8015  # this is the vanilla server port, not the riffle one


rootDoc = """
usage: paradrop [options] <command> [<args>...]
        
options:
   -h, --help
   --version
   -v, --verbose    Show verbose internal output   
   -m, --mode=MODE  production, development, test, or local [default: production]
   
commands:
    router     Manage routers
    chute      Manage chutes
    
    list       List and search for resources you own
    logs       Query logs
    
    login      Log into Paradrop account on another computer
    register   Register for a Paradrop account
    logout     Logout of account on this computer

See 'paradrop <command> -h' for more information on a specific command.    
"""

routerDoc = """
usage: 
    paradrop [options] router create <name> 
    paradrop [options] router provision <name> <host> <port>

options:
   -v, --verbose    Show verbose internal output       

commands: 
    create      Create a new router with the given name
    provision   Assign a newly created router identity to a physical instance
"""

chuteDoc = """
usage:
    paradrop chute install <host> <port> <path-to-config>
    paradrop chute delete <host> <port> <name>
    paradrop chute start <host> <port> <name>
    paradrop chute stop <host> <port> <name>

commands: 
    start       Start the installed chute with the given name
    stop        Stop the installed chute with the given name
    install     Installs and starts a chute on the given router
    delete      Delete the installed chute on the given router
"""

listDoc = """
usage: 
    paradrop list

options:
   -v, --verbose    Show verbose internal output       


Lists all owned resources.
"""

logsDoc = """
usage: 
    paradrop logs <name>

options:
   -v, --verbose    Show verbose internal output       

    
Displays the logs for the provided resource. The resource, commonly a router, 
must be online.
"""


def routerMenu():
    args = docopt(routerDoc, options_first=False)

    if args['provision']:
        return routers.provisionRouter(args['<name>'], args['<host>'], args['<port>'])

    elif args['create']:
        return server.createRouter(args['<name>'])

    else:
        print routerDoc


def chuteMenu():
    args = docopt(chuteDoc, options_first=False)

    if args['install']:
        return routers.installChute(args['<host>'], args['<port>'], args['<path-to-config>'])

    if args['delete']:
        return routers.deleteChute(args['<host>'], args['<port>'], args['<name>'])

    if args['start']:
        return routers.startChute(args['<host>'], args['<port>'], args['<name>'])

    if args['stop']:
        return routers.stopChute(args['<host>'], args['<port>'], args['<name>'])

    print routerDoc


def listMenu():
    args = docopt(listDoc)

    return server.list()


def logsMenu():
    args = docopt(logsDoc)

    return server.logs(args['<name>'])

###################################################################
# Utility and Initialization
###################################################################


class Nexus(nexus.NexusBase):

    '''
    Core nexus subclass. This handles all the high level operations for 
    tools, but should be the lightest of the three nexus subclasses by far. 

    The only core piece of functionality here is logins and handling bad connections.
    '''

    def __init__(self, mode, settings=[]):
        # get a Mode.production, Mode.test, etc from the passed string
        mode = eval('nexus.Mode.%s' % mode)

        # Want to change logging functionality? See optional args on the base class and pass them here
        super(Nexus, self).__init__(nexus.Type.tools, mode, settings=settings, stealStdio=False, printToConsole=True)

    def onStart(self):
        super(Nexus, self).onStart()

    def onStop(self):
        super(Nexus, self).onStop()


@inlineCallbacks
def connectAndCall(command):
    '''
    Convenience method-- wait for nexus to finish connecting and then 
    make the call. 

    The subhandler methods should not call reactor.stop, just return.
    '''

    try:
        yield nexus.core.connect(cxbr.BaseSession)

        # Unpublished
        if command == 'ping':
            yield general.ping()

        # Check for a sub-command. If found, pass off execution to the appropriate sub-handler
        elif command in 'router chute list logs'.split():
            yield eval('%sMenu' % command)()

        else:
            print "%r is not a paradrop command. See 'paradrop -h'." % command
    except:
        e = sys.exc_info()[0]
        print e.usage

    reactor.stop()


def main():
    # present documentation, extract arguments
    args = docopt(rootDoc, version=get_distribution('pdtools').version, options_first=True, help=True)
    argv = [args['<command>']] + args['<args>']
    command = args['<command>']

    print args
    # exit(0)

    # Create and assign the root nexus object
    nexus.core = Nexus('local')

    # TODO: If not provisioned, we have to change our realm into the unprovisioned one

    if command == 'login':
        task.react(server.login, (SERVER_HOST, SERVER_PORT,))

    if command == 'register':
        task.react(server.register, (SERVER_HOST, SERVER_PORT,))

    # if not nexus.core.provisioned():
    #     print 'You must login first.'
    #     exit(0)

    if not store.loggedIn():
        print 'You must login first.'
        return

    # Start the reactor, start the nexus connection, and then start the call
    reactor.callLater(0, connectAndCall, args['<command>'])
    reactor.run()


if __name__ == '__main__':
    main()
