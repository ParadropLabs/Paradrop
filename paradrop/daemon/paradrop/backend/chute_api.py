"""
Install and manage chutes on the host.

Endpoints for these functions can be found under /api/v1/chutes.
"""

import json
import os
import re
import subprocess
import tarfile
import tempfile

import six

from autobahn.twisted.resource import WebSocketResource
from klein import Klein

from paradrop.base import pdutils, settings
from paradrop.base.output import out
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.config import resource
from paradrop.core.container.chutecontainer import ChuteContainer
from paradrop.lib.utils import pdosq

from . import cors
from . import hostapd_control


class ChuteCacheEncoder(json.JSONEncoder):
    """
    JSON encoder for chute cache dictionary.

    The chute cache can contain arbitrary objects, some of which may not be
    JSON-serializable.  This encoder returns handles unserializable objects by
    returning the `repr` string.
    """
    def default(self, o):
        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            return repr(o)


class ChuteEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            return o.__dict__


class UpdateEncoder(json.JSONEncoder):
    def default(self, o):
        result = {
            'created': o.createdTime,
            'responses': o.responses,
            'failure': o.failure
        }
        return result


def tarfile_is_safe(tar):
    """
    Check the names of files in the archive for safety.

    Returns True if all paths are relative and safe or False if
    any of the paths are absolute (leading slash) or try to access
    parent directories (leading ..).
    """
    for member in tar:
        # normpath is useful here because it correctly normalizes "a/../../c"
        # to "../c".
        path = os.path.normpath(member.name)
        if os.path.isabs(path) or path.startswith(".."):
            return False
    return True


def extract_tarred_chute(data):
    tar = tarfile.TarFile(fileobj=data)
    if not tarfile_is_safe(tar):
        raise Exception("Tarfile contains unsafe paths")

    tempdir = tempfile.mkdtemp()
    tar.extractall(tempdir)

    configfile = os.path.join(tempdir, "paradrop.yaml")
    if not os.path.isfile(configfile):
        raise Exception("No paradrop.yaml file found in chute source")

    paradrop_yaml = pdosq.read_yaml_file(configfile, default={})

    return (tempdir, paradrop_yaml)


def chute_access_allowed(request, chute):
    # Allow caller to pass either chute object or the name of a chute.
    if isinstance(chute, six.string_types):
        chute = ChuteStorage.chuteList.get(chute, None)

    # All users are allowed to install a chute if it does not conflict with an
    # existing one.
    if chute is None:
        return True

    # Only an admin or a chute owner are allowed to modify an existing chute.
    if request.user == chute.get_owner() or request.user.role in ["owner", "admin"]:
        return True
    else:
        return False


def permission_denied(request):
    request.setResponseCode(403)
    return json.dumps({
        "error": "You do not have permission to access the requested chute."
    })


class ChuteApi(object):
    routes = Klein()

    def __init__(self, update_manager):
        self.update_manager = update_manager

    @routes.route('/', methods=['GET'])
    def get_chutes(self, request):
        """
        List installed chutes.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             {
               "environment": {},
               "name": "hello-world",
               "allocation": {
                 "cpu_shares": 1024,
                 "prioritize_traffic": false
               },
               "state": "running",
               "version": "x1511808778",
               "resources": null
             }
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        chuteStorage = ChuteStorage()
        chutes = chuteStorage.getChuteList()
        allocation = resource.computeResourceAllocation(chutes)

        result = []
        for chute in chutes:
            service_info = {}
            for service in chute.get_services():
                container_name = service.get_container_name()
                container = ChuteContainer(container_name)

                service_info[service.name] = {
                    'allocation': allocation.get(container_name, None),
                    'state': container.getStatus()
                }

            chute_info = {
                'name': chute.name,
                'owner': chute.get_owner(),
                'state': chute.state,
                'services': service_info,
                'version': getattr(chute, 'version', None),
                'environment': getattr(chute, 'environment', None),
                'resources': getattr(chute, 'resources', None)
            }

            result.append(chute_info)

        return json.dumps(result, cls=ChuteEncoder)

    @routes.route('/', methods=['POST'])
    def create_chute(self, request):
        cors.config_cors(request)

        update = dict(updateClass='CHUTE',
                      updateType='create',
                      user=request.user,
                      tok=pdutils.timeint())

        ctype = request.requestHeaders.getRawHeaders('Content-Type',
                default=[None])[0]
        if ctype == "application/x-tar":
            workdir, paradrop_yaml = extract_tarred_chute(request.content)
            config = paradrop_yaml.get("config", {})

            # Try to read chute name from top level (preferred) or from config
            # object (deprecated).
            if 'name' in paradrop_yaml:
                update['name'] = paradrop_yaml['name']
            elif 'name' in config:
                out.warn("Deprecated: move chute name to top level of config file.")
                update['name'] = config['name']
            else:
                raise Exception("Chute name not found in configuration file.")

            update['workdir'] = workdir
            update.update(config)
        else:
            # TODO: this case is not tested
            body = json.loads(request.content.read())
            config = body['config']
            update.update(config)

        # Set a time-based version number for side-loaded chutes because we do
        # not expect the to receive it from the config file.
        update['version'] = "x{}".format(update['tok'])

        # We will return the change ID to the caller for tracking and log
        # retrieval.
        update['change_id'] = self.update_manager.assign_change_id()

        self.update_manager.add_update(**update)

        result = {
            'change_id': update['change_id']
        }
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(result)

    @routes.route('/<chute>', methods=['GET'])
    def get_chute(self, request, chute):
        """
        Get information about an installed chute.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/hello-world

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "environment": {},
             "name": "hello-world",
             "allocation": {
               "cpu_shares": 1024,
               "prioritize_traffic": false
             },
             "state": "running",
             "version": "x1511808778",
             "resources": null
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
        except KeyError:
            request.setResponseCode(404)
            return "{}"

        if not chute_access_allowed(request, chute_obj):
            return permission_denied(request)

        chuteStorage = ChuteStorage()
        allocation = resource.computeResourceAllocation(
                chuteStorage.getChuteList())

        service_info = {}
        for service in chute_obj.get_services():
            container_name = service.get_container_name()
            container = ChuteContainer(container_name)

            service_info[service.name] = {
                'allocation': allocation.get(container_name, None),
                'state': container.getStatus()
            }

        result = {
            'name': chute,
            'state': chute_obj.state,
            'services': service_info,
            'version': getattr(chute_obj, 'version', None),
            'environment': getattr(chute_obj, 'environment', None),
            'resources': getattr(chute_obj, 'resources', None)
        }

        return json.dumps(result, cls=ChuteEncoder)

    @routes.route('/<chute>', methods=['PUT'])
    def update_chute(self, request, chute):
        cors.config_cors(request)

        if not chute_access_allowed(request, chute):
            return permission_denied(request)

        update = dict(updateClass='CHUTE',
                      updateType='update',
                      tok=pdutils.timeint(),
                      user=request.user,
                      name=chute)

        ctype = request.requestHeaders.getRawHeaders('Content-Type',
                default=[None])[0]
        if ctype == "application/x-tar":
            workdir, paradrop_yaml = extract_tarred_chute(request.content)
            config = paradrop_yaml.get("config", {})

            # Try to read chute name from top level (preferred) or from config
            # object (deprecated).
            if 'name' in paradrop_yaml:
                update['name'] = paradrop_yaml['name']
            elif 'name' in config:
                out.warn("Deprecated: move chute name to top level of config file.")
                update['name'] = config['name']
            else:
                raise Exception("Chute name not found in configuration file.")

            update['workdir'] = workdir
            update.update(config)
        else:
            body = json.loads(request.content.read())
            config = body['config']

            update.update(config)

        # Set a time-based version number for side-loaded chutes because we do
        # not expect the to receive it from the config file.
        update['version'] = "x{}".format(update['tok'])

        # We will return the change ID to the caller for tracking and log
        # retrieval.
        update['change_id'] = self.update_manager.assign_change_id()

        self.update_manager.add_update(**update)

        result = {
            'change_id': update['change_id']
        }
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(result)

    @routes.route('/<chute>', methods=['DELETE'])
    def delete_chute(self, request, chute):
        cors.config_cors(request)

        if not chute_access_allowed(request, chute):
            return permission_denied(request)

        update = dict(updateClass='CHUTE',
                      updateType='delete',
                      tok=pdutils.timeint(),
                      user=request.user,
                      name=chute)

        # We will return the change ID to the caller for tracking and log
        # retrieval.
        update['change_id'] = self.update_manager.assign_change_id()

        self.update_manager.add_update(**update)

        result = {
            'change_id': update['change_id']
        }
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(result)

    @routes.route('/<chute>/stop', methods=['POST'])
    def stop_chute(self, request, chute):
        cors.config_cors(request)

        if not chute_access_allowed(request, chute):
            return permission_denied(request)

        update = dict(updateClass='CHUTE',
                      updateType='stop',
                      tok=pdutils.timeint(),
                      user=request.user,
                      name=chute)

        # We will return the change ID to the caller for tracking and log
        # retrieval.
        update['change_id'] = self.update_manager.assign_change_id()

        self.update_manager.add_update(**update)

        result = {
            'change_id': update['change_id']
        }
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(result)

    @routes.route('/<chute>/start', methods=['POST'])
    def start_chute(self, request, chute):
        cors.config_cors(request)

        if not chute_access_allowed(request, chute):
            return permission_denied(request)

        update = dict(updateClass='CHUTE',
                      updateType='start',
                      tok=pdutils.timeint(),
                      user=request.user,
                      name=chute)

        try:
            body = json.loads(request.content.read())

            # Chute environment variables can be replaced during the operation.
            update['environment'] = body['environment']
        except Exception:
            pass

        # We will return the change ID to the caller for tracking and log
        # retrieval.
        update['change_id'] = self.update_manager.assign_change_id()

        self.update_manager.add_update(**update)

        result = {
            'change_id': update['change_id']
        }
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(result)

    @routes.route('/<chute>/restart', methods=['POST'])
    def restart_chute(self, request, chute):
        cors.config_cors(request)

        if not chute_access_allowed(request, chute):
            return permission_denied(request)

        update = dict(updateClass='CHUTE',
                      updateType='restart',
                      tok=pdutils.timeint(),
                      user=request.user,
                      name=chute)

        try:
            body = json.loads(request.content.read())

            # Chute environment variables can be replaced during the operation.
            update['environment'] = body['environment']
        except Exception:
            pass

        # We will return the change ID to the caller for tracking and log
        # retrieval.
        update['change_id'] = self.update_manager.assign_change_id()

        self.update_manager.add_update(**update)

        result = {
            'change_id': update['change_id']
        }
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(result)

    @routes.route('/<chute>/cache', methods=['GET'])
    def get_chute_cache(self, request, chute):
        """
        Get chute cache contents.

        The chute cache is a key-value store used during chute installation.
        It can be useful for debugging the Paradrop platform.
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)

            result = chute_obj.getCacheContents()
            return json.dumps(result, cls=ChuteCacheEncoder)
        except KeyError:
            request.setResponseCode(404)
            return "{}"

    @routes.route('/<chute>/config', methods=['GET'])
    def get_chute_config(self, request, chute):
        """
        Get current chute configuration.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/captive-portal/config

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "net": {
               "wifi": {
                 "dhcp": {
                   "lease": "1h",
                   "limit": 250,
                   "start": 3
                 },
                 "intfName": "wlan0",
                 "options": {
                   "isolate": True
                 },
                 "ssid": "Free WiFi",
                 "type": "wifi"
               }
             }
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            config = chute_obj.create_specification()
            return json.dumps(config)
        except KeyError:
            request.setResponseCode(404)
            return "{}"

    @routes.route('/<chute>/config', methods=['PUT'])
    def set_chute_config(self, request, chute):
        """
        Update the chute configuration and restart to apply changes.

        **Example request**:

        .. sourcecode:: http

           PUT /api/v1/chutes/captive-portal/config
           Content-Type: application/json

           {
             "net": {
               "wifi": {
                 "dhcp": {
                   "lease": "1h",
                   "limit": 250,
                   "start": 3
                 },
                 "intfName": "wlan0",
                 "options": {
                   "isolate": True
                 },
                 "ssid": "Better Free WiFi",
                 "type": "wifi"
               }
             }
           }

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "change_id": 1
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        if not chute_access_allowed(request, chute):
            return permission_denied(request)

        update = dict(updateClass='CHUTE',
                      updateType='restart',
                      tok=pdutils.timeint(),
                      user=request.user,
                      name=chute)

        try:
            body = json.loads(request.content.read())
            update.update(body)
        except Exception:
            pass

        # We will return the change ID to the caller for tracking and log
        # retrieval.
        update['change_id'] = self.update_manager.assign_change_id()

        self.update_manager.add_update(**update)

        result = {
            'change_id': update['change_id']
        }
        return json.dumps(result)

    @routes.route('/<chute>/networks', methods=['GET'])
    def get_networks(self, request, chute):
        """
        Get list of networks configured for the chute.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/captive-portal/networks

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             {
               "interface": "wlan0",
               "type": "wifi",
               "name": "wifi"
             }
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            networkInterfaces = chute_obj.getCache('networkInterfaces')
        except KeyError:
            request.setResponseCode(404)
            return "[]"

        result = []
        for iface in networkInterfaces:
            data = {
                'name': iface['name'],
                'type': iface['type'],
                'interface': iface['internalIntf']
            }
            result.append(data)

        return json.dumps(result)

    @routes.route('/<chute>/networks/<network>', methods=['GET'])
    def get_network(self, request, chute, network):
        """
        Get information about a network configured for the chute.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/captive-portal/networks/wifi

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "interface": "wlan0",
             "type": "wifi",
             "name": "wifi"
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            networkInterfaces = chute_obj.getCache('networkInterfaces')
        except KeyError:
            request.setResponseCode(404)
            return "{}"

        data = {}
        for iface in networkInterfaces:
            if iface['name'] != network:
                continue

            data = {
                'name': iface['name'],
                'type': iface['type'],
                'interface': iface['internalIntf']
            }

        return json.dumps(data)

    @routes.route('/<chute>/networks/<network>/leases', methods=['GET'])
    def get_leases(self, request, chute, network):
        """
        Get current list of DHCP leases for chute network.

        Returns a list of DHCP lease records with the following fields:

        expires
          lease expiration time (seconds since Unix epoch)
        mac_addr
          device MAC address
        ip_addr
          device IP address
        hostname
          name that the device reported
        client_id
          optional identifier supplied by device

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/captive-portal/networks/wifi/leases

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             {
               "client_id": "01:5c:59:48:7d:b9:e6",
               "expires": "1511816276",
               "ip_addr": "192.168.128.64",
               "mac_addr": "5c:59:48:7d:b9:e6",
               "hostname": "paradrops-iPod"
             }
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            externalSystemDir = chute_obj.getCache('externalSystemDir')
        except KeyError:
            request.setResponseCode(404)
            return "[]"

        leasefile = 'dnsmasq-{}.leases'.format(network)
        path = os.path.join(externalSystemDir, leasefile)

        # The format of the dnsmasq leases file is one entry per line with
        # space-separated fields.
        keys = ['expires', 'mac_addr', 'ip_addr', 'hostname', 'client_id']

        try:
            leases = []
            with open(path, 'r') as source:
                for line in source:
                    parts = line.strip().split()
                    leases.append(dict(zip(keys, parts)))
            return json.dumps(leases)

        except IOError:
            # During chute uninstallation, there is a small window where the
            # chute still exists but the leases file has been removed.
            request.setResponseCode(404)
            return "[]"

    @routes.route('/<chute>/networks/<network>/ssid', methods=['GET'])
    def get_ssid(self, request, chute, network):
        """
        Get currently configured SSID for the chute network.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/captive-portal/networks/wifi/ssid

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "ssid": "Free WiFi",
             "bssid": "02:00:08:24:03:dd"
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            networkInterfaces = chute_obj.getCache('networkInterfaces')
        except KeyError:
            request.setResponseCode(404)
            return "{}"

        ifname = None
        for iface in networkInterfaces:
            if iface['name'] == network:
                ifname = iface['externalIntf']
                break

        address = os.path.join(settings.PDCONFD_WRITE_DIR, "hostapd", ifname)
        return hostapd_control.execute(address, command="GET_CONFIG")

    @routes.route('/<chute>/networks/<network>/ssid', methods=['PUT'])
    def set_ssid(self, request, chute, network):
        """
        Change the configured SSID for the chute network.

        The change will not persist after a reboot. If a persistent change is
        desired, you should update the chute configuration instead.

        **Example request**:

        .. sourcecode:: http

           PUT /api/v1/chutes/captive-portal/networks/wifi/ssid
           Content-Type: application/json

           {
             "ssid": "Best Free WiFi"
           }

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "message": "OK"
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            networkInterfaces = chute_obj.getCache('networkInterfaces')
        except KeyError:
            request.setResponseCode(404)
            return "{}"

        ifname = None
        for iface in networkInterfaces:
            if iface['name'] == network:
                ifname = iface['externalIntf']
                break

        body = json.loads(request.content.read())
        if "ssid" not in body:
            raise Exception("ssid required")

        command = "SET ssid {}".format(body['ssid'])
        address = os.path.join(settings.PDCONFD_WRITE_DIR, "hostapd", ifname)
        return hostapd_control.execute(address, command=command)

    @routes.route('/<chute>/networks/<network>/hostapd_status', methods=['GET'])
    def get_hostapd_status(self, request, chute, network):
        """
        Get low-level status information from the access point.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/captive-portal/networks/wifi/hostapd_status

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "olbc_ht": "0",
             "cac_time_left_seconds": "N/A",
             "num_sta_no_short_slot_time": "0",
             "olbc": "1",
             "num_sta_non_erp": "0",
             "ht_op_mode": "0x4",
             "state": "ENABLED",
             "num_sta_ht40_intolerant": "0",
             "channel": "11",
             "bssid[0]": "02:00:08:24:03:dd",
             "ieee80211n": "1",
             "cac_time_seconds": "0",
             "num_sta[0]": "1",
             "ieee80211ac": "0",
             "phy": "phy0",
             "num_sta_ht_no_gf": "1",
             "freq": "2462",
             "num_sta_ht_20_mhz": "1",
             "num_sta_no_short_preamble": "0",
             "secondary_channel": "0",
             "ssid[0]": "Free WiFi",
             "num_sta_no_ht": "0",
             "bss[0]": "vwlan7e1b"
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            networkInterfaces = chute_obj.getCache('networkInterfaces')
        except KeyError:
            request.setResponseCode(404)
            return "{}"

        ifname = None
        for iface in networkInterfaces:
            if iface['name'] == network:
                ifname = iface['externalIntf']
                break

        address = os.path.join(settings.PDCONFD_WRITE_DIR, "hostapd", ifname)
        return hostapd_control.execute(address, command="STATUS")

    @routes.route('/<chute>/networks/<network>/stations', methods=['GET'])
    def get_stations(self, request, chute, network):
        """
        Get detailed information about connected wireless stations.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/captive-portal/networks/wifi/stations

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             {
               "rx_packets": "230",
               "tdls_peer": "no",
               "authenticated": "yes",
               "rx_bytes": "12511",
               "tx_bitrate": "1.0 MBit/s",
               "tx_retries": "0",
               "signal": "-45 [-49, -48] dBm",
               "authorized": "yes",
               "rx_bitrate": "65.0 MBit/s MCS 7",
               "mfp": "no",
               "tx_failed": "0",
               "inactive_time": "4688 ms",
               "mac_addr": "5c:59:48:7d:b9:e6",
               "tx_bytes": "34176",
               "wmm_wme": "yes",
               "preamble": "short",
               "tx_packets": "88",
               "signal_avg": "-44 [-48, -47] dBm"
             }
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            networkInterfaces = chute_obj.getCache('networkInterfaces')
        except KeyError:
            request.setResponseCode(404)
            return "[]"

        ifname = None
        for iface in networkInterfaces:
            if iface['name'] == network:
                ifname = iface['externalIntf']
                break

        cmd = ['iw', 'dev', ifname, 'station', 'dump']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        stations = []
        current = {}

        for line in proc.stdout:
            line = line.strip()

            match = re.match("Station\s+(\S+)\s+.*", line)
            if match is not None:
                current = {
                    'mac_addr': match.group(1)
                }
                stations.append(current)
                continue

            match = re.match("(.*):\s+(.*)", line)
            if match is not None:
                key = match.group(1).lower().replace(' ', '_').replace('/', '_')
                current[key] = match.group(2)

        return json.dumps(stations)

    @routes.route('/<chute>/networks/<network>/stations/<mac>', methods=['GET'])
    def get_station(self, request, chute, network, mac):
        """
        Get detailed information about a connected station.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/chutes/captive-portal/networks/wifi/stations/5c:59:48:7d:b9:e6

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "rx_packets": "230",
             "tdls_peer": "no",
             "authenticated": "yes",
             "rx_bytes": "12511",
             "tx_bitrate": "1.0 MBit/s",
             "tx_retries": "0",
             "signal": "-45 [-49, -48] dBm",
             "authorized": "yes",
             "rx_bitrate": "65.0 MBit/s MCS 7",
             "mfp": "no",
             "tx_failed": "0",
             "inactive_time": "4688 ms",
             "mac_addr": "5c:59:48:7d:b9:e6",
             "tx_bytes": "34176",
             "wmm_wme": "yes",
             "preamble": "short",
             "tx_packets": "88",
             "signal_avg": "-44 [-48, -47] dBm"
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            networkInterfaces = chute_obj.getCache('networkInterfaces')
        except KeyError:
            request.setResponseCode(404)
            return "{}"

        ifname = None
        for iface in networkInterfaces:
            if iface['name'] == network:
                ifname = iface['externalIntf']
                break

        cmd = ['iw', 'dev', ifname, 'station', 'get', mac]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        station = {}

        for line in proc.stdout:
            line = line.strip()

            match = re.match("Station\s+(\S+)\s+.*", line)
            if match is not None:
                station['mac_addr'] = match.group(1)
                continue

            match = re.match("(.*):\s+(.*)", line)
            if match is not None:
                key = match.group(1).lower().replace(' ', '_').replace('/', '_')
                station[key] = match.group(2)

        return json.dumps(station)

    @routes.route('/<chute>/networks/<network>/stations/<mac>', methods=['DELETE'])
    def delete_station(self, request, chute, network, mac):
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            networkInterfaces = chute_obj.getCache('networkInterfaces')
        except KeyError:
            request.setResponseCode(404)
            return "{}"

        ifname = None
        for iface in networkInterfaces:
            if iface['name'] == network:
                ifname = iface['externalIntf']
                break

        cmd = ['iw', 'dev', ifname, 'station', 'del', mac]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        messages = []
        for line in proc.stdout:
            line = line.strip()
            messages.append(line)

        return json.dumps(messages)

    @routes.route('/<chute>/networks/<network>/hostapd_control/ws', branch=True, methods=['GET'])
    def hostapd_control(self, request, chute, network):
        try:
            chute_obj = ChuteStorage.chuteList[chute]
            if not chute_access_allowed(request, chute_obj):
                return permission_denied(request)
            networkInterfaces = chute_obj.getCache('networkInterfaces')
        except KeyError:
            request.setResponseCode(404)
            return ""

        ifname = None
        for iface in networkInterfaces:
            if iface['name'] == network:
                ifname = iface['externalIntf']
                break

        ctrl_iface = os.path.join(settings.PDCONFD_WRITE_DIR, "hostapd", ifname)
        factory = hostapd_control.HostapdControlWSFactory(ctrl_iface)
        factory.setProtocolOptions(autoPingInterval=10, autoPingTimeout=5)
        return WebSocketResource(factory)
