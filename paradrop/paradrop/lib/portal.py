#
# This module serves the static files of the portal
# Reference:
#   http://peak.telecommunity.com/DevCenter/PkgResources#resourcemanager-api
#   https://manuelnaranjo.com/2011/07/06/serving-static-content-from-egg-files-with-twisted/
# 
#

from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.web.server import Site
from twisted.internet import reactor
from pkg_resources import resource_filename

from paradrop.lib import settings
from pdtools.lib.output import out

def startPortal():
    path = resource_filename('paradrop', 'static')
    root = File(path)
    factory = Site(root)
    reactor.listenTCP(settings.PORTAL_SERVER_PORT, factory)
