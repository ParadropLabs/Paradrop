"""Paradrop build tools.

Usage:
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
    paradrop logs <host> <port>
    paradrop echo <host> <port>
    paradrop (-h | --help)
    paradrop --version
Options:
    -h --help     Show this screen.
    --version     Show version.
"""

from docopt import docopt
from twisted.internet import task

from pdtools.lib import output
from pdtools.coms import routers, general, server
from pdtools.lib.store import store


def main():
    # For now, don't grab STDIO and don't write random log noise to conosle
    output.out.startLogging(stealStdio=False, printToConsole=False)

    args = docopt(__doc__, version='Paradrop build tools v0.1')

    host, port = args['<host>'], args['<port>']

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

    if args['logs']:
        task.react(general.logs, (host, port))

    if args['echo']:
        task.react(general.echo, (host, port))

    if args['login']:
        task.react(server.login)

    if args['register']:
        task.react(server.register)

    # logged in calls
    if not store.loggedIn():
        print 'You must login first.'
        return

    if args['list']:
        task.react(server.ownership)

    if args['router-create']:
        task.react(server.createRouter, (args['<name>'],))

    if args['router-provision']:
        task.react(routers.provisionRouter, (args['<name>'], args['<host>'], args['<port>']))

    print 'Something broke'

if __name__ == '__main__':
    main()
