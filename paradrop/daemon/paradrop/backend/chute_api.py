import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import yaml

from klein import Klein
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

from paradrop.base import pdutils
from paradrop.base.output import out
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.config import resource
from paradrop.core.container.chutecontainer import ChuteContainer
from . import cors


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
        except TypeError as error:
            return repr(o)


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


class ChuteApi(object):
    routes = Klein()

    def __init__(self, update_manager):
        self.update_manager = update_manager

    @routes.route('/', methods=['GET'])
    def get_chutes(self, request):
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        chuteStorage = ChuteStorage()
        chutes = chuteStorage.getChuteList()
        allocation = resource.computeResourceAllocation(chutes)

        result = []
        for chute in chutes:
            container = ChuteContainer(chute.name)

            result.append({
                'name': chute.name,
                'state': container.getStatus(),
                'version': getattr(chute, 'version', None),
                'allocation': allocation.get(chute.name, None),
                'environment': getattr(chute, 'environment', None),
                'resources': getattr(chute, 'resources', None)
            })

        return json.dumps(result)

    @routes.route('/', methods=['POST'])
    @inlineCallbacks
    def create_chute(self, request):
        cors.config_cors(request)

        update = dict(updateClass='CHUTE',
                      updateType='create',
                      tok=pdutils.timeint())

        ctype = request.requestHeaders.getRawHeaders('Content-Type',
                default=[None])[0]
        if ctype == "application/x-tar":
            tar = tarfile.TarFile(fileobj=request.content)
            if not tarfile_is_safe(tar):
                raise Exception("Tarfile contains unsafe paths")

            tempdir = tempfile.mkdtemp()
            tar.extractall(tempdir)

            configfile = os.path.join(tempdir, "paradrop.yaml")
            if not os.path.isfile(configfile):
                raise Exception("No paradrop.yaml file found in chute source")

            with open(configfile, "r") as source:
                full_config = yaml.safe_load(source)
                config = full_config.get("config", {})

            # Try to read chute name from top level (preferred) or from config
            # object (deprecated).
            if 'name' in full_config:
                update['name'] = full_config['name']
            elif 'name' in config:
                out.warn("Deprecated: move chute name to top level of config file.")
                update['name'] = config['name']
            else:
                raise Exception("Chute name not found in configuration file.")

            update['workdir'] = tempdir
            update.update(config)

        else:
            body = json.loads(request.content.read())
            config = body['config']
            update.update(config)

        # Set a time-based version number for side-loaded chutes because we do
        # not expect the to receive it from the config file.
        update['version'] = "x{}".format(update['tok'])

        result = yield self.update_manager.add_update(**update)
        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))

    @routes.route('/<chute>', methods=['GET'])
    def get_chute(self, request, chute):
        cors.config_cors(request)

        request.setHeader('Content-Type', 'application/json')

        chute_obj = ChuteStorage.chuteList[chute]
        container = ChuteContainer(chute)

        chuteStorage = ChuteStorage()
        allocation = resource.computeResourceAllocation(
                chuteStorage.getChuteList())

        result = {
            'name': chute,
            'state': container.getStatus(),
            'version': getattr(chute_obj, 'version', None),
            'allocation': allocation.get(chute, None),
            'environment': getattr(chute_obj, 'environment', None),
            'resources': getattr(chute_obj, 'resources', None)
        }

        return json.dumps(result)

    @routes.route('/<chute>', methods=['PUT'])
    @inlineCallbacks
    def update_chute(self, request, chute):
        cors.config_cors(request)

        update = dict(updateClass='CHUTE',
                      updateType='update',
                      tok=pdutils.timeint(),
                      name=chute)

        ctype = request.requestHeaders.getRawHeaders('Content-Type',
                default=[None])[0]
        if ctype == "application/x-tar":
            tar = tarfile.TarFile(fileobj=request.content)
            if not tarfile_is_safe(tar):
                raise Exception("Tarfile contains unsafe paths")

            tempdir = tempfile.mkdtemp()
            tar.extractall(tempdir)

            configfile = os.path.join(tempdir, "paradrop.yaml")
            if not os.path.isfile(configfile):
                raise Exception("No paradrop.yaml file found in chute source")

            with open(configfile, "r") as source:
                full_config = yaml.safe_load(source)
                config = full_config.get("config", {})

            # Try to read chute name from top level (preferred) or from config
            # object (deprecated).
            if 'name' in full_config:
                update['name'] = full_config['name']
            elif 'name' in config:
                out.warn("Deprecated: move chute name to top level of config file.")
                update['name'] = config['name']
            else:
                raise Exception("Chute name not found in configuration file.")

            update['workdir'] = tempdir
            update.update(config)

        else:
            body = json.loads(request.content.read())
            config = body['config']

            update.update(config)

        # Set a time-based version number for side-loaded chutes because we do
        # not expect the to receive it from the config file.
        update['version'] = "x{}".format(update['tok'])

        result = yield self.update_manager.add_update(**update)
        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))

    @routes.route('/<chute>', methods=['DELETE'])
    @inlineCallbacks
    def delete_chute(self, request, chute):
        cors.config_cors(request)

        update = dict(updateClass='CHUTE',
                      updateType='delete',
                      tok=pdutils.timeint(),
                      name=chute)
        result = yield self.update_manager.add_update(**update)

        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))

    @routes.route('/<chute>/stop', methods=['POST'])
    @inlineCallbacks
    def stop_chute(self, request, chute):
        cors.config_cors(request)

        update = dict(updateClass='CHUTE',
                      updateType='stop',
                      tok=pdutils.timeint(),
                      name=chute)
        result = yield self.update_manager.add_update(**update)

        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))

    @routes.route('/<chute>/start', methods=['POST'])
    @inlineCallbacks
    def start_chute(self, request, chute):
        cors.config_cors(request)

        update = dict(updateClass='CHUTE',
                      updateType='start',
                      tok=pdutils.timeint(),
                      name=chute)
        result = yield self.update_manager.add_update(**update)

        request.setHeader('Content-Type', 'application/json')
        returnValue(json.dumps(result, cls=UpdateEncoder))

    @routes.route('/<chute>/cache', methods=['GET'])
    def get_chute_cache(self, request, chute):
        """
        Get chute cache contents.

        The chute cache is a key-value store used during chute installation.
        It can be useful for debugging the Paradrop platform.
        """
        cors.config_cors(request)

        request.setHeader('Content-Type', 'application/json')

        chute_obj = ChuteStorage.chuteList[chute]
        result = chute_obj.getCacheContents()

        return json.dumps(result, cls=ChuteCacheEncoder)

    @routes.route('/<chute>/networks', methods=['GET'])
    def get_networks(self, request, chute):
        cors.config_cors(request)

        request.setHeader('Content-Type', 'application/json')

        chute_obj = ChuteStorage.chuteList[chute]
        networkInterfaces = chute_obj.getCache('networkInterfaces')

        result = []
        for iface in networkInterfaces:
            data = {
                'name': iface['name'],
                'type': iface['netType'],
                'interface': iface['internalIntf']
            }
            result.append(data)

        return json.dumps(result)

    @routes.route('/<chute>/networks/<network>', methods=['GET'])
    def get_network(self, request, chute, network):
        cors.config_cors(request)

        request.setHeader('Content-Type', 'application/json')

        chute_obj = ChuteStorage.chuteList[chute]
        networkInterfaces = chute_obj.getCache('networkInterfaces')

        data = {}
        for iface in networkInterfaces:
            if iface['name'] != network:
                continue

            data = {
                'name': iface['name'],
                'type': iface['netType'],
                'interface': iface['internalIntf']
            }

        return json.dumps(data)

    @routes.route('/<chute>/networks/<network>/leases', methods=['GET'])
    def get_leases(self, request, chute, network):
        """
        Get current list of DHCP leases for chute network.

        Returns a list of DHCP lease records with the following fields:
        expires: lease expiration time (seconds since Unix epoch)
        mac_addr: device MAC address
        ip_addr: device IP address
        hostname: name that the device reported
        client_id: optional identifier supplied by device
        """
        cors.config_cors(request)

        request.setHeader('Content-Type', 'application/json')

        chute_obj = ChuteStorage.chuteList[chute]
        externalSystemDir = chute_obj.getCache('externalSystemDir')

        leasefile = 'dnsmasq-{}.leases'.format(network)
        path = os.path.join(externalSystemDir, leasefile)

        # The format of the dnsmasq leases file is one entry per line with
        # space-separated fields.
        keys = ['expires', 'mac_addr', 'ip_addr', 'hostname', 'client_id']

        leases = []
        with open(path, 'r') as source:
            for line in source:
                parts = line.strip().split()
                leases.append(dict(zip(keys, parts)))

        return json.dumps(leases)

    @routes.route('/<chute>/networks/<network>/stations', methods=['GET'])
    def get_stations(self, request, chute, network):
        cors.config_cors(request)

        request.setHeader('Content-Type', 'application/json')

        chute_obj = ChuteStorage.chuteList[chute]
        networkInterfaces = chute_obj.getCache('networkInterfaces')

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
        cors.config_cors(request)

        request.setHeader('Content-Type', 'application/json')

        chute_obj = ChuteStorage.chuteList[chute]
        networkInterfaces = chute_obj.getCache('networkInterfaces')

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

        chute_obj = ChuteStorage.chuteList[chute]
        networkInterfaces = chute_obj.getCache('networkInterfaces')

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
