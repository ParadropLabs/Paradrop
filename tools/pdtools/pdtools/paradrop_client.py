import base64
import getpass
import os
import re

import builtins
import requests

from .devices.camera import Camera


LOCAL_DEFAULT_USERNAME = "paradrop"
LOCAL_DEFAULT_PASSWORD = ""

PARADROP_API_TOKEN = os.environ.get("PARADROP_API_TOKEN", None)
PARADROP_CHUTE_NAME = os.environ.get("PARADROP_CHUTE_NAME", None)


class ParadropClient(object):
    """
    Client for interacting with a Paradrop daemon instance.

    Here is a motivating example that is intended to be valid chute code:

    from pdtools import ParadropClient
    client = ParadropClient()
    for camera in client.get_cameras():
        img = camera.get_image()
    """
    def __init__(self, host=None):
        if host is None:
            host = "172.17.0.1"

        self.host = host
        self.base_url = "http://{}/api/v1".format(host)

    def get_cameras(self, chute_name=PARADROP_CHUTE_NAME, network_name=None):
        """
        List cameras connected to a chute's network.

        Note: This only detects the subset of D-Link cameras that we currently
        support. We will add more devices as we test them.

        chute_name: if not specified, will be read from PARADROP_CHUTE_NAME
        network_name: if not specified, will include all of the chute's networks
        """
        if chute_name is None:
            raise Exception("chute_name was not specified")

        cameras = []
        leases = self.get_leases(chute_name, network_name)

        dlink_re = re.compile("(28:10:7b|b0:c5:54|01:b0:c5):.*")
        for lease in leases:
            match = dlink_re.match(lease['mac_addr'])
            if match is not None:
                cameras.append(Camera(lease['mac_addr'], lease['ip_addr']))

        return cameras

    def get_leases(self, chute_name=PARADROP_CHUTE_NAME, network_name=None):
        """
        List DHCP lease records for a chute's network.

        chute_name: if not specified, will be read from PARADROP_CHUTE_NAME
        network_name: if not specified, will include all of the chute's networks
        """
        if chute_name is None:
            raise Exception("chute_name was not specified")

        networks = []
        devices = []

        if network_name is not None:
            networks = [network_name]
        else:
            netlist = self.get_networks(chute_name)

            # In rare cases, get_networks returns None early in the chute
            # lifetime. Instead of causing an exception, treat it as an empty
            # list - no cameras detected yet.
            if netlist is not None:
                networks = [x['name'] for x in netlist]

        for net in networks:
            url = self.base_url + "/chutes/{}/networks/{}/leases".format(
                    chute_name, net)
            result = self.request("GET", url)
            if isinstance(result, list):
                devices.extend(result)

        return devices

    def get_networks(self, chute_name=PARADROP_CHUTE_NAME):
        """
        List networks owned by a chute.

        chute_name: if not specified, will be read from PARADROP_CHUTE_NAME
        """
        if chute_name is None:
            raise Exception("chute_name was not specified")

        url = self.base_url + "/chutes/{}/networks".format(chute_name)
        result = self.request("GET", url)

        return result

    def request(self, method, url, json=None, headers=None, **kwargs):
        """
        Issue a router API request.

        This will prompt for a username and password if necessary.
        """
        session = requests.Session()
        request = requests.Request(method, url, json=json, headers=headers, **kwargs)

        # TODO: Implement selectable auth methods including:
        # - API token from environment variable
        # - Default username and password
        # - Prompt for username and password

        # First try with the default username and password.
        # If that fails, prompt user and try again.
        userpass = "{}:{}".format(LOCAL_DEFAULT_USERNAME, LOCAL_DEFAULT_PASSWORD)

        encoded = base64.b64encode(userpass.encode('utf-8')).decode('ascii')
        session.headers.update({'Authorization': 'Basic {}'.format(encoded)})

        prepped = session.prepare_request(request)

        while True:
            res = session.send(prepped)
            if res.status_code == 401:
                username = builtins.input("Username: ")
                password = getpass.getpass("Password: ")
                userpass = "{}:{}".format(username, password).encode('utf-8')
                encoded = base64.b64encode(userpass.encode('utf-8')).decode('ascii')

                session.headers.update({'Authorization': 'Basic {}'.format(encoded)})
                prepped = session.prepare_request(request)

            elif res.ok:
                return res.json()

            else:
                return None
