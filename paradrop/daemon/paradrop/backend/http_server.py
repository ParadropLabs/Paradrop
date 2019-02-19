'''
The HTTP server to serve local portal and provide RESTful APIs
'''

import os
import pkg_resources
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from klein import Klein
from autobahn.twisted.resource import WebSocketResource

from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.system.system_status import SystemStatus

from .airshark_api import AirsharkApi
from .airshark_ws import AirsharkSpectrumFactory, AirsharkAnalyzerFactory
from .audio_api import AudioApi
from .auth import requires_auth, AuthApi
from .change_api import ChangeApi
from .change_ws import ChangeStreamFactory
from .chute_api import ChuteApi
from .chute_log_ws import ChuteLogWsFactory
from .config_api import ConfigApi
from .information_api import InformationApi
from .log_sockjs import LogSockJSFactory
from .network_api import NetworkApi
from .paradrop_log_ws import ParadropLogWsFactory
from .password_api import PasswordApi
from .password_manager import PasswordManager
from .snapd_resource import SnapdResource
from .status_sockjs import StatusSockJSFactory
from .token_manager import TokenManager


class HttpServer(object):
    app = Klein()

    def __init__(self, update_manager, update_fetcher, airshark_manager, portal_dir=None):
        self.update_manager = update_manager
        self.update_fetcher = update_fetcher
        self.system_status = SystemStatus()
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager()
        self.airshark_manager = airshark_manager

        if portal_dir:
            self.portal_dir = portal_dir
        elif 'SNAP' in os.environ:
            self.portal_dir = os.environ['SNAP'] + '/www'
        else:
            self.portal_dir = pkg_resources.resource_filename('paradrop', 'static')


    @app.route('/api/v1/audio', branch=True)
    def api_audio(self, request):
        return AudioApi().routes.resource()


    @app.route('/api/v1/auth', branch=True)
    def api_auth(self, request):
        return AuthApi(self.password_manager, self.token_manager).routes.resource()


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


    @app.route('/api/v1/network', branch=True)
    @requires_auth
    def api_network(self, request):
        return NetworkApi().routes.resource()


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
        chute = ChuteStorage.get_chute(name)
        factory = LogSockJSFactory(chute)
        factory.setProtocolOptions(autoPingInterval=5, autoPingTimeout=2)
        return WebSocketResource(factory)


    @app.route('/sockjs/status', branch=True)
    @requires_auth
    def status(self, request):
        #cors.config_cors(request)
        factory = StatusSockJSFactory(self.system_status)
        factory.setProtocolOptions(autoPingInterval=5, autoPingTimeout=2)
        return WebSocketResource(factory)


    @app.route('/ws/chute_logs/<string:name>', branch=True)
    @requires_auth
    def chute_logs(self, request, name):
        #cors.config_cors(request)
        chute = ChuteStorage.get_chute(name)
        factory = ChuteLogWsFactory(chute)
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
    endpoint = serverFromString(
        reactor,
        "tcp:port={0}:interface={1}".format(port, host)
    )
    endpoint.listen(Site(http_server.app.resource()))


def annotate_routes(router, prefix):
    """
    Annotate klein routes for compatibility with autoflask generator.
    """
    router.static_path = ""
    router.view_functions = router.endpoints
    for rule in router.url_map.iter_rules():
        rule.doc_prefix = prefix


annotate_routes(AudioApi.routes, "/api/v1/audio")
annotate_routes(ChuteApi.routes, "/api/v1/chutes")
annotate_routes(ConfigApi.routes, "/api/v1/config")
annotate_routes(InformationApi.routes, "/api/v1/info")
