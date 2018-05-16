"""
Get information about network devices.

Endpoints for these functions can be found under /api/v1/network.
"""

import fnmatch
import json
import os

from klein import Klein

from paradrop.base import settings
from paradrop.lib.utils import parsing

from . import cors


def read_leases(path):
    """
    Read leases from a dnsmasq leases file.

    Returns a list of leases, each a dictionary containing the following fields.
    as_of: Time that lease information was last updated (seconds since Unix epoch).
    expires: DHCP expiration time (seconds since Unix epoch).
    mac_addr: MAC address of the device.
    ip_addr: IP address assigned to the device.
    hostname: Device hostname if reported.
    client_id: A client-specified identifier, which varies between devices.
    """
    # The format of the dnsmasq leases file is one entry per line with
    # space-separated fields.
    keys = ['expires', 'mac_addr', 'ip_addr', 'hostname', 'client_id']

    leases = []

    # Get mtime of the leases file, which gives a sense of the age.
    as_of = os.path.getmtime(path)

    with open(path, "r") as source:
        for line in source:
            parts = line.strip().split()
            entry = dict(zip(keys, parts))
            entry['as_of'] = as_of
            entry['expires'] = parsing.str_to_numeric(entry['expires'])

            # Note: I considered filtering out expired leases based on the
            # expiration time, but apparently dnsmasq leaves old expiration
            # times in this file even for active devices.
            leases.append(entry)

    return leases


def update_lease(leases, entry):
    """
    Update a dictionary of DHCP leases with a new entry.

    The dictionary should be indexed by MAC address. The new entry will be
    added to the dictionary unless it would replace an entry for the same MAC
    address from a more recent lease file.
    """
    mac_addr = entry['mac_addr']
    if mac_addr in leases:
        existing = leases[mac_addr]

        if existing['as_of'] >= entry['as_of']:
            return existing

    leases[mac_addr] = entry
    return entry


class NetworkApi(object):
    routes = Klein()

    def __init__(self):
        pass

    @routes.route("/devices", methods=["GET"])
    def get_devices(self, request):
        """
        List connected devices.
        """

        """
        Get detailed information about connected wireless stations.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/network/devices

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             {
               "as_of": 1511806276,
               "client_id": "01:5c:59:48:7d:b9:e6",
               "expires": 1511816276,
               "ip_addr": "192.168.128.64",
               "mac_addr": "5c:59:48:7d:b9:e6",
               "hostname": "paradrops-iPod"
             }
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        leases = {}

        for root, dirs, files in os.walk(settings.RUNTIME_HOME_DIR):
            for file in fnmatch.filter(files, "dnsmasq-*.leases"):
                path = os.path.join(root, file)

                for entry in read_leases(path):
                    update_lease(leases, entry)

        return json.dumps(leases.values())
