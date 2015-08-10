'''
usage:
    paradrop login
    paradrop register
    paradrop install <host> <port> <path-to-config> 
    paradrop delete <host> <port> <chute-name>
    paradrop start <host> <port> <chute-name>
    paradrop stop <host> <port> <chute-name>
    paradrop snap-install <host> <port>
    paradrop router-create <name>
    paradrop router-provision <name> <host> <port>
    paradrop list
    paradrop logs <name>
    paradrop echo <host> <port>
    paradrop (-h | --help)
    paradrop --version

options:
    -h --help     Show this screen.
    --version     Show version.
'''

from pkg_resources import get_distribution

from docopt import docopt
from twisted.internet import task
from twisted.internet import reactor

from pdtools.lib import output, riffle, names
from pdtools.coms import routers, general, server
from pdtools.lib.store import store

SERVER_HOST = 'paradrop.io'
# SERVER_HOST = 'localhost'
SERVER_PORT = 8015  # this is the vanilla server port, not the riffle one


def main():
    # show the documentation and extract host and port if provided (since they are commonly used)
    args = docopt(__doc__, version=get_distribution('pdtools').version)
    host, port = args['<host>'], args['<port>']
    port = int(port) if port else None

    setup()

    # Make it happen.
    if args['install']:
        return routers.installChute(args['<host>'], args['<port>'], args['<path-to-config>'])

    if args['delete']:
        return routers.deleteChute(args['<host>'], args['<port>'], args['<chute-name>'])

    if args['start']:
        return routers.startChute(args['<host>'], args['<port>'], args['<chute-name>'])

    if args['stop']:
        return routers.stopChute(args['<host>'], args['<port>'], args['<chute-name>'])

    if args['snap-install']:
        print 'Not implemented. Sorry, love.'

    if args['login']:
        task.react(server.login, (SERVER_HOST, SERVER_PORT,))

    if args['register']:
        task.react(server.register, (SERVER_HOST, SERVER_PORT,))

    # logged in calls
    if not store.loggedIn():
        print 'You must login first.'
        return

    if args['logs']:
        reactor.callLater(.1, server.logs, None, args['<name>'])
        reactor.run()
        return

    if args['echo']:
        task.react(general.echo, (host, port))

    if args['list']:
        task.react(server.list)

    if args['router-create']:
        task.react(server.createRouter, (args['<name>'],))

    if args['router-provision']:
        task.react(routers.provisionRouter, (args['<name>'], args['<host>'], args['<port>']))

    print 'Something broke'


def setup():
    '''
    Boilerplate setup. Start the logger, give riffle crypto keys, and 
    initialize riffle's portal by creating name to realm assignments
    '''
    # For now, don't grab STDIO and don't write random log noise to conosle
    output.out.startLogging(stealStdio=False, printToConsole=False)

    # Initialize riffle with default values (can be overridden later)
    riffle.portal.certCa = store.getKey('ca.pem')
    riffle.portal.keyPrivate = store.getKey('client.pem')
    riffle.portal.host = SERVER_HOST
    # NOTE: riffle serves on its own default port. This is a different port from the const above

    # Register realms. See riffle documentation for Realm in pdtools.lib.riffle
    riffle.portal.addRealm(names.matchers[names.NameTypes.server], riffle.Realm(server.ServerPerspective))
    riffle.portal.addRealm(names.matchers[names.NameTypes.router], riffle.Realm(riffle.RifflePerspective))


###################################################################
# New Docs (currently incomplete)
###################################################################

rootDoc = """
usage: git [--version] [--exec-path=<path>] [--html-path]
           [-p|--paginate|--no-pager] [--no-replace-objects]
           [--bare] [--git-dir=<path>] [--work-tree=<path>]
           [-c <name>=<value>] [--help]
           <command> [<args>...]

options:
   -c <name=value>
   -h, --help
   -p, --paginate

The most commonly used git commands are:
   add        Add file contents to the index
   branch     List, create, or delete branches
   checkout   Checkout a branch or paths to the working tree
   clone      Clone a repository into a new directory
   commit     Record changes to the repository
   push       Update remote refs along with associated objects
   remote     Manage set of tracked repositories

See 'git help <command>' for more information on a specific command.

"""
routerDoc = """
usage: paradrop router provision
       paradrop router list

    -v, --verbose         be verbose; must be placed before a subcommand

Other Content!
    Look!
"""


def routerMenu(argv):
    args = docopt(routerDoc)
    print args


def main2():
    ''' Show documentation and branch appropriately '''
    # show the documentation and extract host and port if provided (since they are commonly used)
    args = docopt(rootDoc, version=get_distribution('pdtools').version)

    # host, port = args['<host>'], args['<port>']
    # port = int(port) if port else None
    argv = [args['<command>']] + args['<args>']

    if args['<command>'] == 'remote':
        # routerMenu(argv)
        args = docopt(routerDoc)
        print args


if __name__ == '__main__':
    main2()
