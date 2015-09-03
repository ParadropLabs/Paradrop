'''
Entry point for client tools.

This module has two logical sections: extracting and validating arguments, and 
sending program flow into the correct function.

Structurally there are three sections. In order:
    - Literal docstrings users see
    - Subcommand handlers
    - Entry point

The main method calls docopt.docopt, which parses the first positional command given.
If that command matches a sub-command the correct handler is invoked. 

docopt.docopt will not allow execution to continue if the args matcher fails (in other words:
dont worry about failure conditions.) Check documentation for more information.

To run this code from the command line:
    export PDCONFD_WRITE_DIR="/tmp/pdconfd"
    export UCI_CONFIG_DIR="/tmp/config.d"
'''

from pkg_resources import get_distribution
import sys

import docopt
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from pdtools.lib import cxbr, nexus
from pdtools.coms import routers, general, server

SERVER_HOST = 'paradrop.io'
# SERVER_HOST = 'localhost'
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
    logout     Logout of account on this computer (not implemented)

See 'paradrop <command> -h' for more information on a specific command.    
"""

routerDoc = """
usage: 
    paradrop [options] router create <name> 
    paradrop [options] router provision <name> <host> <port>
    paradrop [options] router update <name> <snap> ...
    paradrop [options] router ping <name>
    paradrop [options] router getConfig <name>
    paradrop [options] router setConfig <name> <path-to-config>

options:
   -v, --verbose    Show verbose internal output       
   -m, --mode=MODE  production, development, test, or local [default: production]

commands: 
    create      Create a new router with the given name
    provision   Assign a newly created router identity to a physical instance
"""

chuteDoc = """
usage:
    paradrop [options] chute install <host> <port> <path-to-config>
    paradrop [options] chute delete <host> <port> <name>
    paradrop [options] chute start <host> <port> <name>
    paradrop [options] chute stop <host> <port> <name>

options:
   -v, --verbose    Show verbose internal output 
   -m, --mode=MODE  production, development, test, or local [default: production]

commands: 
    start       Start the installed chute with the given name
    stop        Stop the installed chute with the given name
    install     Installs and starts a chute on the given router
    delete      Delete the installed chute on the given router
"""

listDoc = """
usage: 
    paradrop [options] list

options:
   -v, --verbose    Show verbose internal output 
   -m, --mode=MODE  production, development, test, or local [default: production]


Lists all owned resources.
"""

logsDoc = """
usage: 
    paradrop [options] logs <name>

options:
   -v, --verbose    Show verbose internal output 
   -m, --mode=MODE  production, development, test, or local [default: production]      

    
Displays the logs for the provided resource. The resource, commonly a router, 
must be online.
"""


def routerMenu(s):
    args = docopt.docopt(routerDoc, options_first=False)

    if args['provision']:
        return routers.provisionRouter(args['<name>'], args['<host>'], args['<port>'])

    elif args['create']:
        return server.createRouter(args['<name>'])

    elif args['update']:
        return routers.update(args['<name>'], args['<snap>'])

    elif args['ping']:
        return routers.ping(args['<name>'])

    elif args['getConfig']:
        return routers.getConfig(args['<name>'])

    elif args['setConfig']:
        return routers.setConfig(args['<name>'], args['<path-to-config>'])

    else:
        print routerDoc


def chuteMenu(s):
    args = docopt.docopt(chuteDoc, options_first=False)

    host, port = args['<host>'], args['<port>']

    if args['install']:
        return routers.installChute(host, port, args['<path-to-config>'])

    if args['delete']:
        return routers.deleteChute(host, port, args['<name>'])

    if args['start']:
        return routers.startChute(host, port, args['<name>'])

    if args['stop']:
        return routers.stopChute(host, port, args['<name>'])

    print routerDoc


def listMenu(s):
    args = docopt.docopt(listDoc)

    return server.list()


def logsMenu(s):
    args = docopt.docopt(logsDoc)

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

    def __init__(self, mode, verbose, settings=[]):
        super(Nexus, self).__init__(nexus.Type.tools, mode, settings=settings, stealStdio=False, printToConsole=verbose)


def connectAndCall(command):
    '''
    Wait for nexus to connect, make the requested calls. 
    '''

    d = nexus.core.connect(cxbr.BaseSession, debug=False)

    # If not provisioned, user is not logged in. User can still login, cant proceed further
    if command == 'login':
        d.addCallback(server.login)

    if command == 'register':
        d.addCallback(server.register)

    if not nexus.core.provisioned():
        print 'You must login first.'
        exit(0)

    # Unpublished
    if command == 'ping':
        d.addCallback(general.ping)

    # Check for a sub-command. If found, pass off execution to the appropriate sub-handler
    elif command in 'router chute list logs'.split():
        d.addCallback(eval('%sMenu' % command))

    else:
        print "%r is not a paradrop command. See 'paradrop -h'." % command

    # Catch the docopt exceptions and print them. This is usage information.
    def showDocopt(x):
        if isinstance(x.value, docopt.DocoptExit):
            print x.value
            return None

        return x

    d.addErrback(showDocopt)
    d.addErrback(general.printFailure)
    d.addBoth(lambda x: reactor.stop())


def main():
    # present documentation, extract arguments
    args = docopt.docopt(rootDoc, version=get_distribution('pdtools').version, options_first=True, help=True)
    argv = [args['<command>']] + args['<args>']
    command = args['<command>']

    # Create the global nexus object and assign it as a global "singleton"
    nexus.core = Nexus(args['--mode'], args['--verbose'])

    # Start the reactor, start the nexus connection, and then start the call
    reactor.callLater(0, connectAndCall, command)
    reactor.run()


if __name__ == '__main__':
    main()
