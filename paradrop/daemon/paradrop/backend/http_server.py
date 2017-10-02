'''
The HTTP server to serve local portal and provide RESTful APIs
'''

import json
import os
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.proxy import ReverseProxyResource
from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.internet.protocol import Factory
from klein import Klein
from txsockjs.factory import SockJSResource
from autobahn.twisted.resource import WebSocketResource

from paradrop.base.exceptions import ParadropException
from paradrop.core.container.chutecontainer import ChuteContainer
from paradrop.core.system.system_status import SystemStatus

from .auth import requires_auth
from .information_api import InformationApi
from .change_api import ChangeApi
from .change_ws import ChangeStreamFactory
from .config_api import ConfigApi
from .chute_api import ChuteApi
from .password_api import PasswordApi
from .airshark_api import AirsharkApi
from .log_sockjs import LogSockJSFactory
from .chute_log_ws import ChuteLogWsFactory
from .status_sockjs import StatusSockJSFactory
from .airshark_ws import AirsharkSpectrumFactory, AirsharkAnalyzerFactory
from .password_manager import PasswordManager
from .snapd_resource import SnapdResource
from .paradrop_log_ws import ParadropLogWsFactory
from . import cors

class HttpServer(object):
    app = Klein()

    def __init__(self, update_manager, update_fetcher, airshark_manager, portal_dir=None):
        self.update_manager = update_manager
        self.update_fetcher = update_fetcher
        self.system_status = SystemStatus()
        self.password_manager = PasswordManager()
        self.airshark_manager = airshark_manager

        if portal_dir:
            self.portal_dir = portal_dir
        elif 'SNAP' in os.environ:
            self.portal_dir = os.environ['SNAP'] + '/www'
        else:
            self.portal_dir = resource_filename('paradrop', 'static')


    @app.route('/api/v1/info', branch=True)
    @requires_auth
    def api_information(self, request):
        return InformationApi().routes.resource()


    @app.route('/api/v1/changes/', branch=True)
    @requires_auth
    def api_changes(self, request):
        return ChangeApi(self.update_manager).routes.resource()


    @app.route('/api/v1/config', branch=True)
    @requires_auth
    def api_configuration(self, request):
        return ConfigApi(self.update_manager, self.update_fetcher).routes.resource()


    @app.route('/api/v1/chutes/', branch=True)
    @requires_auth
    def api_chute(self, request):
        return ChuteApi(self.update_manager).routes.resource()


    @app.route('/api/v1/password', branch=True)
    @requires_auth
    def api_password(self, request):
        return PasswordApi(self.password_manager).routes.resource()


    @app.route('/api/v1/airshark', branch=True)
    @requires_auth
    def api_airshark(self, request):
        return AirsharkApi(self.airshark_manager).routes.resource()


    @app.route('/snapd/', branch=True)
    @requires_auth
    def snapd(self, request):
        return SnapdResource()


    '''
    # Not being used for now because we are using HAProxy to setup the reverse proxy
    @app.route('/chutes/<string:name>', branch=True)
    def chutes(self, request, name):
        try:
            container = ChuteContainer(name)
            ip = container.getIP()
            return ReverseProxyResource(ip, 80, '/')
        except ParadropException as error:
            return str(error)
    '''

    @app.route('/sockjs/logs/<string:name>', branch=True)
    @requires_auth
    def logs(self, request, name):
        #cors.config_cors(request)
        options = {
            'websocket': True,
            'heartbeat': 5,
            'timeout': 2,
        }
        return SockJSResource(LogSockJSFactory(name), options)


    @app.route('/sockjs/status', branch=True)
    @requires_auth
    def status(self, request):
        #cors.config_cors(request)
        options = {
            'websocket': True,
            'heartbeat': 5,
            'timeout': 2,
        }
        return SockJSResource(StatusSockJSFactory(self.system_status), options)


    @app.route('/ws/chute_logs/<string:name>', branch=True)
    @requires_auth
    def chute_logs(self, request, name):
        #cors.config_cors(request)
        factory = ChuteLogWsFactory(name)
        factory.setProtocolOptions(autoPingInterval=10, autoPingTimeout=5)
        return WebSocketResource(factory)


    @app.route('/ws/airshark/analyzer', branch=True)
    @requires_auth
    def airshark_analyzer(self, request):
        #cors.config_cors(request)
        factory = AirsharkAnalyzerFactory(self.airshark_manager)
        factory.setProtocolOptions(autoPingInterval=10, autoPingTimeout=5)
        return WebSocketResource(factory)


    @app.route('/ws/airshark/spectrum', branch=True)
    @requires_auth
    def airshark_spectrum(self, request):
        #cors.config_cors(request)
        factory = AirsharkSpectrumFactory(self.airshark_manager)
        factory.setProtocolOptions(autoPingInterval=10, autoPingTimeout=5)
        return WebSocketResource(factory)

    @app.route('/ws/paradrop_logs', branch=True)
    @requires_auth
    def paradrop_logs(self, request):
        #cors.config_cors(request)
        factory = ParadropLogWsFactory()
        factory.setProtocolOptions(autoPingInterval=10, autoPingTimeout=5)
        return WebSocketResource(factory)

    @app.route('/ws/changes/<int:change_id>/stream', branch=True)
    @requires_auth
    def change_stream(self, request, change_id):
        change = self.update_manager.find_change(change_id)
        if change is not None:
            factory = ChangeStreamFactory(change)
            factory.setProtocolOptions(autoPingInterval=10, autoPingTimeout=5)
            return WebSocketResource(factory)
        else:
            request.setResponseCode(404)
            return "{}"


    @app.route('/', branch=True)
    @requires_auth
    def home(self, request):
        return File(self.portal_dir)


def setup_http_server(http_server, host, port):
    endpoint_description = "tcp:port={0}:interface={1}".format(port,
                                                               host)
    endpoint = serverFromString(
        reactor,
        "tcp:port={0}:interface={1}".format(port, host)
    )
    endpoint.listen(Site(http_server.app.resource()))
