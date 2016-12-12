#
# This module serves the static files of the portal
# Reference:
#   http://peak.telecommunity.com/DevCenter/PkgResources#resourcemanager-api
#   https://manuelnaranjo.com/2011/07/06/serving-static-content-from-egg-files-with-twisted/
# 
#

import os
#from pkg_resources import resource_filename

from twisted.internet import reactor
from twisted.web.proxy import ReverseProxyResource
from twisted.web.resource import Resource, NoResource
from twisted.web.server import Site
from twisted.web.static import File

from paradrop.base.output import out
from paradrop.base.exceptions import ParadropException
from paradrop.base import settings
from paradrop.lib.container import dockerapi


class ChuteErrorPage(Resource):
    isLeaf = True

    def __init__(self, error):
        Resource.__init__(self)
        self.error = error

    def render(self, request):
        return str(self.error)


class ParadropPortal(Resource):
    isLeaf = False

    def __init__(self, portal_dir=None):
        Resource.__init__(self)
        if portal_dir:
            path = portal_dir
        else:
            path = os.environ['SNAP'] + '/www'
        self.static = File(path)

    def getChild(self, path, request):
        host = request.getHeader(b'host')

        parts = host.split(':')
        name = parts[0]

        if name == 'home.paradrop.org':
            return self.static.getChild(path, request)

        elif name.endswith('.home.paradrop.org'):
            parts = name.split('.')
            chute = parts[0]
            try:
                ip = dockerapi.getChuteIP(chute)
                # According to the twisted docs, we should NOT add a leading slash
                # to the path, but it doesn't work unless we do.
                return ReverseProxyResource(ip, 80, '/' + path)
            except ParadropException as error:
                return ChuteErrorPage(error)

        else:
            # Handle the case where someone tries the router's IP address
            # directly.  Just give them the router portal.
            return self.static.getChild(path, request)


def startPortal(portal_dir):
    router = ParadropPortal(portal_dir)
    factory = Site(router)
    reactor.listenTCP(settings.PORTAL_SERVER_PORT, factory)
