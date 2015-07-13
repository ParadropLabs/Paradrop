"""Paradrop build tools.

Usage:
    paradrop install <host> <port> <path-to-config> 
    paradrop snap-install <host> <port>
    paradrop logs <host> <port>
    paradrop echo <host> <port>
    paradrop (-h | --help)
    paradrop --version
Options:
    -h --help     Show this screen.
    --version     Show version.
"""


import requests
import os
import json

from pdtools.coms.client import RpcClient

from twisted.internet import reactor
from twisted.internet import defer
from docopt import docopt


def main():
    # args = createArgs().parse_args()
    # print(args)

    args = docopt(__doc__, version='Paradrop build tools v0.1')
    # print(args)

    if args['install']:
        installChute(args['<host>'], args['<port>'], args['<path-to-config>'])

    if args['snap-install']:
        print 'Not implemented. Sorry, love.'

    if args['logs']:
        logs(args['<host>'], args['<port>'])

    if args['echo']:
        echo(args['<host>'], args['<port>'])


def installChute(host, port, config):
    '''
    Testing method. Take a git url from github and load it onto snappy-pd. 
    '''

    print 'Installing chute'

    # path = os.abspath(directory)

    # The project directory can either be cloned to the backend or installed locally,
    # doesn't matter which one-- we still have to stream the files over

    params = {'config': config}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/create', data=json.dumps(params))
    print r.text_


def logs(host, port):
    '''
    Connect to the named router.

    TODO: convert from host/port to finding the router by its name. 
    '''

    RpcClient(host, port, 'internal').log().addCallbacks(printSuccess, printFailure).addBoth(killReactor)
    reactor.run()


def echo(host, port):
    RpcClient(host, port, 'internal').echo('Hello!').addCallbacks(printSuccess, printFailure).addBoth(killReactor)
    reactor.run()


def installParadrop():
    ''' Testing method. Install paradrop, snappy, etc onto SD card '''
    pass

###############################################################################
# Default Callbacks
###############################################################################


def killReactor(r):
    reactor.stop()


def printSuccess(r):
    print r


def printFailure(r):
    print 'Failed!'
    print r

if __name__ == '__main__':
    main()
