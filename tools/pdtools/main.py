"""
Paradrop command line utility.

Usage:
    pdtools routers list
    pdtools routers create <name> [--orphaned] [--claim=<ct>]
    pdtools routers delete <router_id>
    pdtools local <router_addr> chute list
    pdtools local <router_addr> chute <chute> start
    pdtools local <router_addr> chute <chute> stop
    pdtools local <router_addr> chute <chute> delete
    pdtools local <router_addr> chute <chute> info
    pdtools local <router_addr> chute <chute> cache
    pdtools local <router_addr> chute <chute> create
    pdtools local <router_addr> chute <chute> update
    pdtools local <router_addr> hostconfig
    pdtools local <router_addr> hostconfig edit
    pdtools local <router_addr> hostconfig change <option> <value>
    pdtools local <router_addr> sshkeys
    pdtools local <router_addr> sshkeys add <path>
    pdtools local <router_addr> pdconf
    pdtools local <router_addr> pdconf reload
    pdtools local <router_addr> password
    pdtools local <router_addr> provision <router_id> <router_password> [--server=<server>] [--wamp=<wamp>]
    pdtools local <router_addr> networks <chute>
    pdtools local <router_addr> stations <chute> <network>

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
import operator
import os
import tarfile
import tempfile
import yaml
from pprint import pprint

import builtins
from docopt import docopt
import requests


PDSERVER_URL = os.environ.get('PDSERVER_URL', 'https://paradrop.org')

LOCAL_DEFAULT_USERNAME = "paradrop"
LOCAL_DEFAULT_PASSWORD = ""


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


def router_request(method, url, json=None, headers=None, dump=True, **kwargs):
    """
    Issue a router API request.

    This will prompt for a username and password if necessary.
    """
    session = requests.Session()
    request = requests.Request(method, url, json=json, headers=headers, **kwargs)

    # First try with the default username and password.
    # If that fails, prompt user and try again.
    userpass = "{}:{}".format(LOCAL_DEFAULT_USERNAME, LOCAL_DEFAULT_PASSWORD)
    encoded = base64.b64encode(userpass).decode('ascii')
    session.headers.update({'Authorization': 'Basic {}'.format(encoded)})

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

        else:
            if res.ok and dump:
                data = res.json()
                pprint(data)
            return res


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


def chute_tree(router_addr, arguments):
    """
    Handle functions related to chutes.
    """
    if arguments['list']:
        url = "http://{}/api/v1/chutes/".format(router_addr)
        router_request("GET", url)

    elif arguments['start']:
        name = arguments['<chute>']
        url = "http://{}/api/v1/chutes/{}/start".format(router_addr, name)
        data = {
            'config': {
                'name': arguments['<chute>']
            }
        }
        router_request("POST", url, json=data)

    elif arguments['stop']:
        name = arguments['<chute>']
        url = "http://{}/api/v1/chutes/{}/stop".format(router_addr, name)
        data = {
            'config': {
                'name': arguments['<chute>']
            }
        }
        router_request("POST", url, json=data)

    elif arguments['delete']:
        name = arguments['<chute>']
        url = "http://{}/api/v1/chutes/{}".format(router_addr, name)
        data = {
            'config': {
                'name': arguments['<chute>']
            }
        }
        router_request("DELETE", url, json=data)

    elif arguments['info']:
        chute = arguments['<chute>']
        url = "http://{}/api/v1/chutes/{}".format(router_addr, chute)
        router_request("GET", url)

    elif arguments['cache']:
        chute = arguments['<chute>']
        url = "http://{}/api/v1/chutes/{}/cache".format(router_addr, chute)
        router_request("GET", url)

    elif arguments['create']:
        chute = arguments['<chute>']
        url = "http://{}/api/v1/chutes/".format(router_addr)
        headers = {'Content-Type': 'application/x-tar'}

        if not os.path.exists("paradrop.yaml"):
            raise Exception("No paradrop.yaml file found in working directory.")

        with tempfile.TemporaryFile() as temp:
            tar = tarfile.open(fileobj=temp, mode="w")
            for dirName, subdirList, fileList in os.walk('.'):
                for fname in fileList:
                    path = os.path.join(dirName, fname)
                    arcname = os.path.normpath(path)
                    tar.add(path, arcname=arcname)
            tar.close()

            temp.seek(0)
            router_request("POST", url, headers=headers, data=temp)

    elif arguments['update']:
        chute = arguments['<chute>']
        url = "http://{}/api/v1/chutes/{}".format(router_addr, chute)
        headers = {'Content-Type': 'application/x-tar'}

        if not os.path.exists("paradrop.yaml"):
            raise Exception("No paradrop.yaml file found in working directory.")

        with tempfile.TemporaryFile() as temp:
            tar = tarfile.open(fileobj=temp, mode="w")
            for dirName, subdirList, fileList in os.walk('.'):
                for fname in fileList:
                    path = os.path.join(dirName, fname)
                    arcname = os.path.normpath(path)
                    tar.add(path, arcname=arcname)
            tar.close()

            temp.seek(0)
            router_request("PUT", url, headers=headers, data=temp)


def hostconfig_tree(router_addr, arguments):
    """
    Handle functions related to the router host configuration.
    """
    url = "http://{}/api/v1/config/hostconfig".format(router_addr)

    if arguments['change']:
        req = router_request("GET", url, dump=False)
        config = req.json()
        change_json(config, arguments['<option>'], arguments['<value>'])
        data = {
            'config': config
        }
        router_request("PUT", url, json=data)

    elif arguments['edit']:
        req = router_request("GET", url, dump=False)
        config = req.json()

        fd, path = tempfile.mkstemp()
        os.close(fd)

        with open(path, 'w') as output:
            output.write(yaml.safe_dump(config, default_flow_style=False))

        # Get modified time before calling editor.
        orig_mtime = os.path.getmtime(path)

        editor = os.environ.get("EDITOR", "vim")
        os.spawnvpe(os.P_WAIT, editor, [editor, path], os.environ)

        with open(path, 'r') as source:
            data = source.read()
            config = yaml.safe_load(data)

        # Check if the file has been modified, and if it has, send the update.
        new_mtime = os.path.getmtime(path)
        if new_mtime != orig_mtime:
            data = {
                'config': config
            }
            router_request("PUT", url, json=data)

        os.remove(path)

    else:
        router_request("GET", url)


def sshkeys_tree(router_addr, arguments):
    """
    Handle functions related to router SSH authorized keys.
    """
    url = "http://{}/api/v1/config/sshKeys".format(router_addr)

    if arguments['add']:
        with open(arguments['<path>'], 'r') as source:
            key_string = source.read().strip()
        data = {
            'key': key_string
        }
        router_request("POST", url, json=data)

    else:
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


def networks(router_addr, arguments):
    """
    List a chute's networks.
    """
    url = "http://{}/api/v1/chutes/{}/networks".format(router_addr,
            arguments['<chute>'])

    router_request("GET", url)


def stations(router_addr, arguments):
    """
    List stations connected to a chute's network.
    """
    url = "http://{}/api/v1/chutes/{}/networks/{}/stations".format(router_addr,
            arguments['<chute>'], arguments['<network>'])

    router_request("GET", url)


def pdconf(router_addr, arguments):
    """
    Access the pdconf subsystem.
    """
    url = "http://{}/api/v1/config/pdconf".format(router_addr)

    if arguments['reload']:
        res = router_request("PUT", url, dump=False)
    else:
        res = router_request("GET", url, dump=False)

    if res.ok:
        data = res.json()
        data.sort(key=operator.itemgetter("age"))

        print("{:3s} {:12s} {:20s} {:30s} {:5s}".format("Age", "Type", "Name",
            "Comment", "Pass"))
        for item in data:
            print("{age:<3d} {type:12s} {name:20s} {comment:30s} {success}".format(**item))


def local_tree(arguments):
    """
    Handle functions related to router API.
    """
    router_addr = arguments['<router_addr>']
    if arguments['chute']:
        chute_tree(router_addr, arguments)
    elif arguments['hostconfig']:
        hostconfig_tree(router_addr, arguments)
    elif arguments['sshkeys']:
        sshkeys_tree(router_addr, arguments)
    elif arguments['password']:
        password_tree(router_addr, arguments)
    elif arguments['provision']:
        provision(router_addr, arguments)
    elif arguments['networks']:
        networks(router_addr, arguments)
    elif arguments['stations']:
        stations(router_addr, arguments)
    elif arguments['pdconf']:
        pdconf(router_addr, arguments)


def main():
    """
    pdtools main function.
    """
    arguments = docopt(__doc__)
    if arguments['routers']:
        routers_tree(arguments)
    elif arguments['local']:
        local_tree(arguments)


if __name__ == "__main__":
    main()
