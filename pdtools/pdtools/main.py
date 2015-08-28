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

from docopt import docopt
from twisted.internet import task
from twisted.internet import reactor

from pdtools.lib import output, riffle, names, cxbr
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

    checkLoggedIn()

    if args['provision']:
        task.react(routers.provisionRouter, (args['<name>'], args['<host>'], args['<port>']))

    elif args['create']:
        task.react(server.createRouter, (args['<name>'],))

    else:
        print routerDoc


def chuteMenu():
    args = docopt(chuteDoc, options_first=False)

    checkLoggedIn()

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
    checkLoggedIn()

    task.react(server.list)


def logsMenu():
    args = docopt(logsDoc)
    checkLoggedIn()

    reactor.callLater(.1, server.logs, None, args['<name>'])
    reactor.run()
    exit(0)


###################################################################
# Utility and Initialization
###################################################################

def checkLoggedIn():
    # logged in calls
    if not store.loggedIn():
        print 'You must login first.'
        exit(0)


def setup(displayToConsole=False, logLevel=0):
    '''
    Boilerplate setup. Start the logger, give riffle crypto keys, and 
    initialize riffle's portal by creating name to realm assignments
    '''
    # For now, don't grab STDIO and don't write random log noise to conosle
    output.out.startLogging(stealStdio=False, printToConsole=False)

    # Initialize riffle with default values (can be overridden later)
    # NOTE: riffle serves on its own default port. This is a different port from the const above
    # riffle.portal.certCa = store.getKey('ca.pem')
    # riffle.portal.keyPrivate = store.getKey('client.pem')
    # riffle.portal.host = SERVER_HOST

    # Register realms. See riffle documentation for Realm in pdtools.lib.riffle
    # riffle.portal.addRealm(names.matchers[names.NameTypes.server], riffle.Realm(server.ServerPerspective))
    # riffle.portal.addRealm(names.matchers[names.NameTypes.router], riffle.Realm(riffle.RifflePerspective))


def main():
    # present documentation, extract arguments
    args = docopt(rootDoc, version=get_distribution('pdtools').version, options_first=True, help=True)
    argv = [args['<command>']] + args['<args>']
    command = args['<command>']

    # Check for verbose flag. If set, turn on the serious logging.
    # TODO: set lower level log filters based on the number of '-v's passed in
    setup(displayToConsole=args['--verbose'])

    if command == 'login':
        task.react(server.login, (SERVER_HOST, SERVER_PORT,))

    if command == 'register':
        task.react(server.register, (SERVER_HOST, SERVER_PORT,))

    # It doesn't matter what the call is. If we got to this point then we have to instantiate a
    # crossbar session
    # pdid = store.getConfig('pdid')
    # sess = yield cxbr.BaseSession.start("ws://127.0.0.1:8080/ws", pdid)

    # Check for a sub-command. If found, pass off execution to the appropriate sub-handler
    if command in 'router chute list logs'.split():
        return eval('%sMenu' % args['<command>'])()

    exit("%r is not a paradrop command. See 'paradrop -h'." % args['<command>'])

if __name__ == '__main__':
    main()
