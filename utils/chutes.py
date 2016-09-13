"""
This tool communicates directly with the router's HTTP configuration API to
perform chute operations.  This is useful while we transition from pdtools to
cloud management.

Usage:
    python chutes.py install <host> <port> <config>
    python chutes.py update <host> <port> <config>
    python chutes.py delete <host> <port> <chute>
    python chutes.py start <host> <port> <chute>
    python chutes.py stop <host> <port> <chute>
"""

import requests
import json
import urllib
import os
import sys
import yaml
from os.path import expanduser


def readChuteConfig(filename):
    # Read local yaml into a config_json to send via post request
    try:
        with open(filename, 'r') as stream:
            config_json = yaml.load(stream)
            config_json['date'] = config_json['date'].isoformat()
    except IOError as e:
        print 'Error: ' + config + ' not found.'
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

    return config_json


###############################################################################
# Chute Operations
###############################################################################


def installChute(host, port, config):
    '''
    Take a local config yaml file and launch chute of given host with pdfcd running on specified port.
    '''
    config_json = readChuteConfig(config)
    if config_json is None:
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


def updateChute(host, port, config):
    '''
    Take a local config yaml file and launch chute of given host with pdfcd running on specified port.
    '''
    config_json = readChuteConfig(config)
    if config_json is None:
        return

    print 'Updating chute...\n'
    params = {'config': config_json}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/update', data=json.dumps(params), stream=True)
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


def printUsage():
    print("Usage: {} <install|update|delete|stop|start> <host> <port> <config>".format(sys.argv[0]))


if __name__ == "__main__":
    if len(sys.argv) < 5:
        printUsage()
        sys.exit(1)

    cmd = sys.argv[1]
    host = sys.argv[2]
    port = sys.argv[3]
    config = sys.argv[4]

    if cmd == "install":
        installChute(host, port, config)
    elif cmd == "update":
        updateChute(host, port, config)
    elif cmd == "delete":
        deleteChute(host, port, config)
    elif cmd == "stop":
        stopChute(host, port, config)
    elif cmd == "start":
        startChute(host, port, config)
    else:
        printUsage()
        sys.exit(1)
