'''
Communication with routers
'''

import requests
import json
import urllib
import os
import yaml
from os.path import expanduser

from twisted.internet import defer

from pdtools.coms import general
from pdtools.coms.client import RpcClient
from pdtools.lib.store import store
from pdtools.lib import pdutils, riffle
from pdtools.lib.output import out


###############################################################################
# Riffle and Non-riffle implementations
###############################################################################

@general.defaultCallbacks
@defer.inlineCallbacks
def provisionRouter(r, name, host, port):

    # Bug: if the user sets the name of the router as their username, this will
    # fail badly
    target = [x for x in store.getConfig('routers') if name in x['_id']]

    if len(target) == 0:
        print 'Router with name ' + name + ' not found.'
        defer.returnValue(None)

    target = target[0]

    pkey = store.getKey(target['_id'] + '.client.pem')
    cacert = store.getKey('ca.pem')

    client = RpcClient(host, port, 'internal')
    ret = yield client.provision(target['_id'], pkey, cacert)

    print 'Provisioning successful'


###############################################################################
# Chute Operations
###############################################################################

def installChute(host, port, config):
    '''
    Take a local config yaml file and launch chute of given host with pdfcd running on specified port.
    '''

    # Read local yaml into a config_json to send via post request
    try:
        with open(config, 'r') as stream:
            config_json = yaml.load(stream)
            config_json['date'] = config_json['date'].isoformat()
    except IOError as e:
        print 'Error: ' + config + ' not found.'
        return

    # Verify the config provided in some way.
    cfg_verf = pdutils.check(config_json, dict, {'dockerfile': dict, 'name': str, 'owner': str})
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

    print 'Installing chute...\n'
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
            except Exception as e:
                print line


def deleteChute(host, port, name):
    '''
    Remove chute with given name from host with pdfcd running on specified port.
    '''

    print 'Removing chute...\n'

    params = {'name': name}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/delete', data=json.dumps(params), stream=True)

    for line in r.iter_lines():
        if line:
            try:
                line = json.loads(line)
                if line.get('success'):
                    print line.get('message')
                else:
                    print 'ERROR: Failed to delete chute.(' + urllib.unquote(str(line.get('message'))) + ')'
            except Exception as e:
                print line


def stopChute(host, port, name):
    '''
    Stop chute with given name from host with pdfcd running on specified port.
    '''

    print 'Stopping chute...\n'

    params = {'name': name}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/stop', data=json.dumps(params), stream=True)

    for line in r.iter_lines():
        if line:
            try:
                line = json.loads(line)
                if line.get('success'):
                    print line.get('message')
                else:
                    print 'ERROR: Failed to stop chute.(' + urllib.unquote(str(line.get('message'))) + ')'
            except Exception as e:
                print line


def startChute(host, port, name):
    '''
    Start chute with given name from host with pdfcd running on specified port.
    '''

    print 'Starting chute...\n'

    params = {'name': name}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/start', data=json.dumps(params), stream=True)

    for line in r.iter_lines():
        if line:
            try:
                line = json.loads(line)
                if line.get('success'):
                    print line.get('message')
                else:
                    print 'ERROR: Failed to start chute.(' + urllib.unquote(str(line.get('message'))) + ')'
            except Exception as e:
                print line
