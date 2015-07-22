'''
Communication with routers
'''

import os
import yaml


from pdtools.coms import general
from pdtools.coms.client import RpcClient
from pdtools.lib.store import store

from twisted.internet import defer

from os.path import expanduser
from pdtools.lib.output import out

import requests
import json
import urllib

from pdtools.lib import pdutils
from pdtools.lib.store import store


@general.defaultCallbacks
@defer.inlineCallbacks
def provisionRouter(r, name, host, port):
    target = [x for x in store.getConfig('routers') if name in x]

    if len(target) == 0:
        print 'Router with name ' + name + ' not found.'
        yield 1
        defer.returnValue(None)

    client = RpcClient(host, port, '')
    ret = yield client.provision(target['_id'], target['publicKey'], target['privateKey'])


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
            except Exception as e:
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
