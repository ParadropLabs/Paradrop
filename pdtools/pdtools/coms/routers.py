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
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

from pdtools.coms import general
from pdtools.coms.client import RpcClient
from pdtools.lib import pdutils, riffle, cxbr, nexus
from pdtools.lib.output import out


@defer.inlineCallbacks
def provisionRouter(name, host, port):

    routers = yield nexus.core.session.call('pd', 'list')
    routers = routers['routers']
    pdid = nexus.core.info.pdid + '.' + name

    # print 'Got list: ' + str(routers)
    for x in routers:
        print x['_id']

    # Bug: if the user sets the name of the router as their username, this will
    # fail badly
    target = filter(lambda x: x['_id'] == pdid, routers)

    if len(target) == 0:
        print 'Router with name ' + name + ' not found.'
        defer.returnValue(None)

    target = target[0]

    pkey = nexus.core.getKey(target['_id'] + '.client.pem')
    cacert = nexus.core.getKey('ca.pem')

    client = RpcClient(host, port, 'internal')
    ret = yield client.provision(target['_id'], pkey, cacert)

    print 'Provisioning successful'


@defer.inlineCallbacks
def update(name, sources):
    print 'Starting an update command!'

    target = nexus.core.info.pdid + '.' + name

    data = {
        'command': 'install',
        'sources': sources
    }

    result = yield nexus.core.session.call(target, 'update', data)
    print 'Conpleted with result: ' + result
    defer.returnValue(result)


@defer.inlineCallbacks
def getConfig(name):
    target = nexus.core.info.pdid + '.' + name
    result = yield nexus.core.session.call(target, 'getConfig')

    config = json.loads(result)
    print(yaml.safe_dump(config, default_flow_style=False))

    defer.returnValue(result)


@defer.inlineCallbacks
def setConfig(name, path):
    with open(path, 'r') as source:
        config = yaml.safe_load(source)

    target = nexus.core.info.pdid + '.' + name

    data = json.dumps(config, separators=(',', ':'))
    result = yield nexus.core.session.call(target, 'setConfig', data)
    defer.returnValue(result)


@defer.inlineCallbacks
def ping(target):
    target = nexus.core.info.pdid + '.' + target
    ret = yield nexus.core.session.call(target, 'ping')
    print 'Ping result: ' + str(ret)

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
