"""
This module exposes device configuration.

Endpoints for these functions can be found under /api/v1/config.
"""

import json
from klein import Klein
from twisted.internet import reactor
from twisted.internet.defer import DeferredList, inlineCallbacks, returnValue

from paradrop.base import constants, nexus, settings
from paradrop.base.output import out
from paradrop.base.pdutils import timeint
from paradrop.core.config import hostconfig
from paradrop.core.agent.http import PDServerRequest
from paradrop.core.agent.provisioning import read_provisioning_result
from paradrop.core.agent.reporting import sendNodeIdentity, sendStateReport
from paradrop.core.agent.wamp_session import WampSession
from paradrop.confd import client as pdconf_client
from paradrop.lib.misc import ssh_keys
from paradrop.lib.misc.governor import GovernorClient

from . import cors


class ConfigApi(object):
    """
    Configuration API.

    This class handles HTTP API calls related to router configuration.
    """

    routes = Klein()

    def __init__(self, update_manager, update_fetcher):
        self.update_manager = update_manager
        self.update_fetcher = update_fetcher

    @routes.route('/hostconfig', methods=['PUT'])
    def update_hostconfig(self, request):
        """
        Replace the device's host configuration.

        **Example request**:

        .. sourcecode:: http

           PUT /api/v1/config/hostconfig
           Content-Type: application/json

           {
             "firewall": {
               "defaults": {
                 "forward": "ACCEPT",
                 "input": "ACCEPT",
                 "output": "ACCEPT"
               }
             },
             ...
           }

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             change_id: 1
           }

        For a complete example, please see the Host Configuration section.
        """
        cors.config_cors(request)
        body = json.loads(request.content.read().decode('utf-8'))
        config = body['config']

        update = dict(updateClass='ROUTER',
                      updateType='sethostconfig',
                      name=constants.RESERVED_CHUTE_NAME,
                      tok=timeint(),
                      hostconfig=config)

        # We will return the change ID to the caller for tracking and log
        # retrieval.
        update['change_id'] = self.update_manager.assign_change_id()

        self.update_manager.add_update(**update)

        result = {
            'change_id': update['change_id']
        }
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(result)

    @routes.route('/hostconfig', methods=['GET'])
    def get_hostconfig(self, request):
        """
        Get the device's current host configuration.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/config/hostconfig

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "firewall": {
               "defaults": {
                 "forward": "ACCEPT",
                 "input": "ACCEPT",
                 "output": "ACCEPT"
               }
             },
             ...
           }

        For a complete example, please see the Host Configuration section.
        """
        cors.config_cors(request)
        config = hostconfig.prepareHostConfig()
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(config, separators=(',',':'))

    @routes.route('/new-config', methods=['GET'])
    def new_config(self, request):
        """
        Generate a new node configuration based on the hardware.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/config/new_config

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "firewall": {
               "defaults": {
                 "forward": "ACCEPT",
                 "input": "ACCEPT",
                 "output": "ACCEPT"
               }
             },
             ...
           }

        For a complete example, please see the Host Configuration section.
        """
        cors.config_cors(request)
        config = hostconfig.prepareHostConfig(hostConfigPath='/dev/null')
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(config, separators=(',',':'))

    @routes.route('/pdid', methods=['GET'])
    def get_pdid(self, request):
        """
        Get the device's current ParaDrop ID. This is the identifier assigned
        by the cloud controller.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/config/pdid

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             pdid: "5890e1e5ab7e317e6c6e049f"
           }
        """
        cors.config_cors(request)
        pdid = nexus.core.info.pdid
        if pdid is None:
            pdid = ""
        request.setHeader('Content-Type', 'application/json')
        return json.dumps({'pdid': pdid})


    @routes.route('/provision', methods=['POST'])
    def provision(self, request):
        """
        Provision the device with credentials from a cloud controller.
        """
        cors.config_cors(request)
        body = json.loads(request.content.read().decode('utf-8'))
        routerId = body['routerId']
        apitoken = body['apitoken']
        pdserver = body['pdserver']
        wampRouter = body['wampRouter']

        changed = False
        if routerId != nexus.core.info.pdid \
            or pdserver != nexus.core.info.pdserver \
            or wampRouter != nexus.core.info.wampRouter:
            if pdserver and wampRouter:
                nexus.core.provision(routerId, pdserver, wampRouter)
            else:
                nexus.core.provision(routerId)
            changed = True

        if apitoken != nexus.core.getKey('apitoken'):
            nexus.core.saveKey(apitoken, 'apitoken')
            changed = True

        if changed:
            PDServerRequest.resetToken()
            nexus.core.jwt_valid = False

            def set_update_fetcher(session):
                session.set_update_fetcher(self.update_fetcher)

            @inlineCallbacks
            def start_polling(result):
                yield self.update_fetcher.start_polling()

            def send_response(result):
                response = dict()
                response['provisioned'] = True
                response['httpConnected'] = nexus.core.jwt_valid
                response['wampConnected'] = nexus.core.wamp_connected
                request.setHeader('Content-Type', 'application/json')
                return json.dumps(response)

            wampDeferred = nexus.core.connect(WampSession)
            wampDeferred.addCallback(set_update_fetcher)

            httpDeferred = sendStateReport()
            httpDeferred.addCallback(start_polling)

            identDeferred = sendNodeIdentity()

            dl = DeferredList([wampDeferred, httpDeferred, identDeferred],
                    consumeErrors=True)
            dl.addBoth(send_response)
            reactor.callLater(6, dl.cancel)
            return dl
        else:
            return json.dumps({'success': False,
                               'message': 'No change on the provision parameters'})

    @routes.route('/provision', methods=['GET'])
    def get_provision(self, request):
        """
        Get the provision status of the device.
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        result = read_provisioning_result()
        result['routerId'] = nexus.core.info.pdid
        result['pdserver'] = nexus.core.info.pdserver
        result['wampRouter'] = nexus.core.info.wampRouter
        apitoken = nexus.core.getKey('apitoken')
        result['provisioned'] = (result['routerId'] is not None and \
                                 apitoken is not None)
        result['httpConnected'] = nexus.core.jwt_valid
        result['wampConnected'] = nexus.core.wamp_connected
        return json.dumps(result)

    @routes.route('/settings', methods=['GET'])
    def get_settings(self, request):
        """
        Get current values of system settings.

        These are the values from paradrop.base.settings. Settings are loaded
        at system initialization from the settings.ini file and environment
        variables. They are intended to be read-only after initialization.

        This endpoint returns the settings as a dictionary with lowercase field
        names.

        Example:
        {
            "portal_server_port": 8080,
            ...
        }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        result = {}
        for name, value in settings.iterate_module_attributes(settings):
            result[name.lower()] = value

        return json.dumps(result)

    @routes.route('/startUpdate', methods=['POST'])
    def start_update(self, request):
        cors.config_cors(request)
        self.update_manager.startUpdate()
        request.setHeader('Content-Type', 'application/json')
        return json.dumps({'success': True})


    @routes.route('/factoryReset', methods=['POST'])
    @inlineCallbacks
    def factory_reset(self, request):
        """
        Initiate the factory reset process.
        """
        cors.config_cors(request)
        update = dict(updateClass='ROUTER',
                      updateType='factoryreset',
                      name='PARADROP',
                      tok=timeint())
        update = yield self.update_manager.add_update(**update)
        returnValue(json.dumps(update.result))

    @routes.route('/pdconf', methods=['GET'])
    def pdconf(self, request):
        """
        Get configuration sections from pdconf.

        This returns a list of configuration sections and whether they were
        successfully applied. This is intended for debugging purposes.
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        return pdconf_client.systemStatus()

    @routes.route('/pdconf', methods=['PUT'])
    def pdconf_reload(self, request):
        """
        Trigger pdconf to reload UCI configuration files.

        Trigger pdconf to reload UCI configuration files and return the status.
        This function is intended for low-level debugging of the paradrop
        pdconf module.
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        return pdconf_client.reloadAll()

    @routes.route('/sshKeys/<user>', methods=['GET', 'POST'])
    def sshKeys(self, request, user):
        """
        Manage list of authorized keys for SSH access.
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        if request.method == "GET":
            try:
                if GovernorClient.isAvailable():
                    client = GovernorClient()
                    keys = client.listAuthorizedKeys(user)

                    # Move keys to the root because the API consumer is
                    # expecting a list, not an object.
                    if 'keys' in keys:
                        keys = keys['keys']
                else:
                    keys = ssh_keys.getAuthorizedKeys(user)
                return json.dumps(keys)
            except Exception as e:
                out.warn(str(e))
                request.setResponseCode(404)
                return json.dumps({'message': str(e)})
        else:
            body = json.loads(request.content.read().decode('utf-8'))
            key = body['key'].strip()

            try:
                if GovernorClient.isAvailable():
                    client = GovernorClient()
                    client.addAuthorizedKey(key, user)
                else:
                    ssh_keys.addAuthorizedKey(key, user)
                return json.dumps(body)
            except Exception as e:
                out.warn(str(e))
                request.setResponseCode(404)
                return json.dumps({'message': str(e)})
