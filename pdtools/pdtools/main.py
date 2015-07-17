"""Paradrop build tools.

Usage:
    paradrop install <host> <port> <path-to-config> 
    paradrop delete <host> <port> <chute-name>
    paradrop start <host> <port> <chute-name>
    paradrop stop <host> <port> <chute-name>
    paradrop snap-install <host> <port>
    paradrop logs <host> <port>
    paradrop echo <host> <port>
    paradrop (-h | --help)
    paradrop --version
Options:
    -h --help     Show this screen.
    --version     Show version.
"""


from docopt import docopt
import requests
import json
import yaml
import urllib

from pdtools.lib import pdutils
from pdtools.lib import output
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

    if args['delete']:
        deleteChute(args['<host>'], args['<port>'], args['<chute-name>'])

    if args['start']:
        startChute(args['<host>'], args['<port>'], args['<chute-name>'])

    if args['stop']:
        stopChute(args['<host>'], args['<port>'], args['<chute-name>'])

    if args['snap-install']:
        print 'Not implemented. Sorry, love.'

    if args['logs']:
        logs(args['<host>'], args['<port>'])

    if args['echo']:
        echo(args['<host>'], args['<port>'])


def installChute(host, port, config):
    '''
    Take a local config yaml file and launch chute of given host with pdfcd running on specified port.
    '''

    # Read local yaml into a config_json to send via post request
    with open(config, 'r') as stream:
        config_json = yaml.load(stream)
        config_json['date'] = config_json['date'].isoformat()

    # Verify the config provided in some way.
    cfg_verf = pdutils.check(config_json, dict, {'dockerfile': dict, 'name': str, 'owner': str, 'host_config': dict})
    if cfg_verf:
        print 'ERROR: ' + cfg_verf
        return

    # Only allowed one way to provide a dockerfile order is local, remote, inline
    if 'local' in config_json['dockerfile']:
        with open(config_json['dockerfile']['local'], 'r') as stream:
            config_json['dockerfile'] = stream.read()
    elif 'remote' in config_json['dockerfile']:
        print 'Remote Dockerfile not supported yet.'
        return
    elif 'inline' in config_json['dockerfile']:
        config_json['dockerfile'] = config_json['dockerfile']['inline']
    else:
        print 'ERROR: No Dockerfile specified in config file.'
        return

    print 'Installing chute...'
    params = {'config': config_json}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/create', data=json.dumps(params), stream=True)
    for line in r.iter_lines():
        if line:
            try:
                line = json.loads(line)
                if line.get('success'):
                    print line.get('message')
                else:
                    print 'ERROR: Failed to install chute.(' + urllib.unquote(str(line.get('message'))) + ')'
            except ValueError as e:
                print line


def deleteChute(host, port, name):
    '''
    Remove chute with given name from host with pdfcd running on specified port.
    '''

    print 'Removing chute...'

    params = {'name': name}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/delete', data=json.dumps(params))

    res = json.loads(r._content)
    if res.get('success'):
        print res.get('message')
    else:
        print 'ERROR: Failed to delete chute.(' + urllib.unquote(str(res.get('message'))) + ')'


def stopChute(host, port, name):
    '''
    Stop chute with given name from host with pdfcd running on specified port.
    '''

    print 'Stopping chute...'

    params = {'name': name}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/stop', data=json.dumps(params))

    res = json.loads(r._content)
    if res.get('success'):
        print res.get('message')
    else:
        print 'ERROR: Failed to stop chute.(' + urllib.unquote(str(res.get('message'))) + ')'


def startChute(host, port, name):
    '''
    Start chute with given name from host with pdfcd running on specified port.
    '''

    print 'Starting chute...'

    params = {'name': name}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/start', data=json.dumps(params))

    res = json.loads(r._content)
    if res.get('success'):
        print res.get('message')
    else:
        print 'ERROR: Failed to start chute.(' + urllib.unquote(str(res.get('message'))) + ')'


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


###############################################################################
#  Inline testing
###############################################################################

def testLogging():
    # initialize the store
    from pdtools.lib import store
    store.store = store.Storage()

    # Connect the store to the output module for file logging
    output.initializeLogger()
    output.out.startLogging(store.LOG_PATH)

    output.out.info("This is a message!")

    output.out.endLogging()


if __name__ == '__main__':
    main()
