'''
The HTTP server to serve local portal and provide RESTful APIs
'''

import json
import os
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.internet.protocol import Factory
from klein import Klein
from txsockjs.factory import SockJSResource

from .information_api import InformationApi
from .config_api import ConfigApi
from .chute_api import ChuteApi
from .status_sock_js_protocol import StatusSockJSProtocol


class HttpServer(object):
    app = Klein()

    def __init__(self, update_manager, update_fetcher, portal_dir=None):
        self.update_manager = update_manager
        self.update_fetcher = update_fetcher

        if portal_dir:
            self.portal_dir = portal_dir
        elif 'SNAP' in os.environ:
            self.portal_dir = os.environ['SNAP'] + '/www'
        else:
            self.portal_dir = resource_filename('paradrop', 'static')


    @app.route('/api/v1/info', branch=True)
    def information(self, request):
        return InformationApi().routes.resource()


    @app.route('/api/v1/config', branch=True)
    def configuration(self, request):
        return ConfigApi(self.update_manager, self.update_fetcher).routes.resource()


    @app.route('/api/v1/chute', branch=True)
    def chute(self, request):
        return ChuteApi(self.update_manager).routes.resource()


    @app.route('/sockjs/status', branch=True)
    def status(self, request):
        return SockJSResource(Factory.forProtocol(StatusSockJSProtocol))


    @app.route('/', branch=True)
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
