"""
Paradrop command line utility.

Usage:
    pdcli routers list
    pdcli routers create <name> [--orphaned] [--claim=<ct>]
    pdcli routers delete <router_id>
    pdcli local <router_addr> chutes list
    pdcli local <router_addr> chutes start <chute>
    pdcli local <router_addr> chutes stop <chute>
    pdcli local <router_addr> chutes delete <chute>
    pdcli local <router_addr> hostconfig
    pdcli local <router_addr> hostconfig change <option> <value>
    pdcli local <router_addr> sshkeys
    pdcli local <router_addr> password
    pdcli local <router_addr> provision <router_id> <router_password> [--server=<server>] [--wamp=<wamp>]

Options:
    router_addr         Router address and optional port (e.g. 10.42.0.150:80).
    router_id           Router ID issued by controller.
    router_password     Router password issued by controller.
    --orphaned          Set router to be in orphaned state (someone can claim it).
    --claim=<ct>        Set router claim token (token allowing one to claim it).
    --server=<server>   Web URL for controller [default: https://paradrop.org].
    --wamp=<wamp>       WAMP URL for message router [default: ws://paradrop.org:9086/ws].

Environment Variables:
    PDSERVER_URL    Paradrop controller URL [default: https://paradrop.org].
"""

from __future__ import print_function

import base64
import getpass
import os
from pprint import pprint

import builtins
from docopt import docopt
import requests


PDSERVER_URL = os.environ.get('PDSERVER_URL', 'https://paradrop.org')


def change_json(data, path, value):
    """
    Replace a value in a JSON object.
    """
    parts = path.split('.')
    head = data
    for i in range(len(parts)-1):
        if isinstance(head, list):
            parts[i] = int(parts[i])
        head = head[parts[i]]
    head[parts[-1]] = value


def pdserver_request(method, url, json=None, headers=None):
    """
    Issue a Paradrop controller API request.

    This will prompt for a username and password if necessary.
    """
    session = requests.Session()

    username = builtins.input('Username: ')
    password = getpass.getpass('Password: ')
    data = {
        'email': username,
        'password': password
    }

    auth_url = '{}/auth/local'.format(PDSERVER_URL)
    request = requests.Request('POST', auth_url, json=data, headers=headers)
    prepped = session.prepare_request(request)
    res = session.send(prepped)
    res_data = res.json()
    token = res_data['token']

    session.headers.update({'Authorization': 'Bearer {}'.format(token)})
    request = requests.Request(method, url, json=json, headers=headers)
    prepped = session.prepare_request(request)

    res = session.send(prepped)
    print("Server responded: {} {}".format(res.status_code, res.reason))
    return res


def router_request(method, url, json=None, headers=None):
    """
    Issue a router API request.

    This will prompt for a username and password if necessary.
    """
    session = requests.Session()
    request = requests.Request(method, url, json=json, headers=headers)
    prepped = session.prepare_request(request)

    while True:
        res = session.send(prepped)
        print("Router responded: {} {}".format(res.status_code, res.reason))
        if res.status_code == 401:
            username = builtins.input("Username: ")
            password = getpass.getpass("Password: ")
            userpass = "{}:{}".format(username, password).encode('utf-8')
            encoded = base64.b64encode(userpass).decode('ascii')

            session.headers.update({'Authorization': 'Basic {}'.format(encoded)})
            prepped = session.prepare_request(request)

        elif res.ok:
            data = res.json()
            pprint(data)
            break


def routers_tree(arguments):
    """
    Handle functions related to the router list.
    """
    router_id = arguments['<router_id>']

    if arguments['list']:
        url = '{}/api/routers'.format(PDSERVER_URL)
        result = pdserver_request('GET', url)
        routers = result.json()

        for router in routers:
            print("{} {} {}".format(router['_id'], router['name'], router['online']))

    elif arguments['create']:
        data = {
            'name': arguments['<name>'],
            'orphaned': False
        }
        if arguments['--orphaned']:
            data['orphaned'] = True
        if arguments['--claim']:
            data['claim_token'] = arguments['--claim']
        pprint(data)

    elif arguments['delete']:
        url = '{}/api/routers/{}'.format(PDSERVER_URL, router_id)
        result = pdserver_request('DELETE', url)


def chutes_tree(router_addr, arguments):
    """
    Handle functions related to chutes.
    """
    if arguments['list']:
        url = "http://{}/api/v1/chutes/get".format(router_addr)
        router_request("GET", url)

    elif arguments['start']:
        url = "http://{}/api/v1/chutes/start".format(router_addr)
        data = {
            'config': {
                'name': arguments['<chute>']
            }
        }
        router_request("PUT", url, json=data)

    elif arguments['stop']:
        url = "http://{}/api/v1/chutes/stop".format(router_addr)
        data = {
            'config': {
                'name': arguments['<chute>']
            }
        }
        router_request("PUT", url, json=data)

    elif arguments['delete']:
        url = "http://{}/api/v1/chutes/delete".format(router_addr)
        data = {
            'config': {
                'name': arguments['<chute>']
            }
        }
        router_request("DELETE", url, json=data)


def hostconfig_tree(router_addr, arguments):
    """
    Handle functions related to the router host configuration.
    """
    url = "http://{}/api/v1/config/hostconfig".format(router_addr)

    if arguments['change']:
        req = requests.get(url)
        config = req.json()
        change_json(config, arguments['<option>'], arguments['<value>'])
        data = {
            'config': config
        }
        router_request("PUT", url, json=data)

    else:
        router_request("GET", url)


def sshkeys_tree(router_addr, arguments):
    """
    Handle functions related to router SSH authorized keys.
    """
    url = "http://{}/api/v1/config/sshKeys".format(router_addr)
    # TODO Implement adding SSH keys.
    router_request("GET", url)


def password_tree(router_addr, arguments):
    """
    Handle functions related to router admin password.
    """
    # TODO: Implement endpoint in router.
    url = "http://{}/api/v1/config/password".format(router_addr)

    username = builtins.input("Username: ")
    while True:
        password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password == confirm:
            break
        else:
            print("Passwords do not match.")

    data = {
        "username": username,
        "password": password
    }
    router_request("PUT", url, json=data)


def provision(router_addr, arguments):
    """
    Provision a router through its API.
    """
    url = "http://{}/api/v1/config/provision".format(router_addr)

    data = {
        'routerId': arguments['<router_id>'],
        'apitoken': arguments['<router_password>'],
        'pdserver': arguments['--server'],
        'wampRouter': arguments['--wamp']
    }
    router_request("POST", url, json=data)


def local_tree(arguments):
    """
    Handle functions related to router API.
    """
    router_addr = arguments['<router_addr>']
    if arguments['chutes']:
        chutes_tree(router_addr, arguments)
    elif arguments['hostconfig']:
        hostconfig_tree(router_addr, arguments)
    elif arguments['sshkeys']:
        sshkeys_tree(router_addr, arguments)
    elif arguments['password']:
        password_tree(router_addr, arguments)
    elif arguments['provision']:
        provision(router_addr, arguments)


def main():
    """
    pdcli main function.
    """
    arguments = docopt(__doc__)
    if arguments['routers']:
        routers_tree(arguments)
    elif arguments['local']:
        local_tree(arguments)


if __name__ == "__main__":
    main()
