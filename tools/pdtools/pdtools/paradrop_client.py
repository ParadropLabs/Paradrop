import base64
import getpass
import os
import re
from pprint import pprint

import builtins
import requests


LOCAL_DEFAULT_USERNAME = "paradrop"
LOCAL_DEFAULT_PASSWORD = ""

PARADROP_API_TOKEN = os.environ.get("PARADROP_API_TOKEN", None)
PARADROP_CHUTE_NAME = os.environ.get("PARADROP_CHUTE_NAME", None)


class ParadropClient(object):
    """
    Client for interacting with a Paradrop daemon instance.
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
        support.

        chute_name: if not specified, will be read from PARADROP_CHUTE_NAME
        network_name: if not specified, will include all of the chute's networks
        """
        if chute_name is None:
            raise Exception("chute_name was not specified")

        cameras = []
        devices = self.get_devices(chute_name, network_name)

        cam_re = re.compile("(28:10:7b|b0:c5:54|01:b0:c5):.*")

        for dev in devices:
            match = cam_re.match(dev['mac_addr'])
            if match is not None:
                cameras.append(dev)

        return cameras

    def get_devices(self, chute_name=PARADROP_CHUTE_NAME, network_name=None):
        """
        List devices connected to a chute's network.

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
            networks = [x['name'] for x in self.get_networks(chute_name)]

        for net in networks:
            url = self.base_url + "/chutes/{}/networks/{}/stations".format(
                    chute_name, net)
            result = self.request("GET", url)

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
