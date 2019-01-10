import os

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET

from paradrop.base import settings
from paradrop.lib.utils.uhttp import UHTTPConnection
from . import cors

class SnapdResource(Resource):
    """
    Expose the snapd API by forwarding requests.

    Changed in 0.13: we try to send the request through the governor service so
    that paradrop can be installed in strict mode.

    https://github.com/snapcore/snapd/wiki/REST-API
    """

    isLeaf = True

    def do_snapd_request(self, request):
        """
        Forward the API request to snapd.
        """
        if os.path.exists(settings.GOVERNOR_INTERFACE):
            interface = settings.GOVERNOR_INTERFACE
            path = '/snapd/' + '/'.join(request.postpath)
        else:
            interface = settings.SNAPD_INTERFACE
            path = '/' + '/'.join(request.postpath)

        body = None
        headers = {}

        # Try to read Content-Type of original request, and set up the body of
        # the request to snapd.  We should expect None for GET requests and
        # JSON for POST requests.
        ctype = request.requestHeaders.getRawHeaders('Content-Type',
                default=[None])[0]
        if ctype is not None:
            headers['Content-Type'] = ctype
            body = request.content.read()

        # Make the request to snapd using a Unix socket.
        conn = UHTTPConnection(interface)
        conn.request(request.method, path, body, headers)
        res = conn.getresponse()
        data = res.read()

        # Return the response to the original request.
        request.setHeader('Content-Type', 'application/json')
        request.write(data)
        request.finish()

    def render(self, request):
        """
        Fulfill requests by forwarding them to snapd.

        We use a synchronous implementation of HTTP over Unix sockets, so we do
        the request in a worker thread and have it call request.finish.
        """
        cors.config_cors(request)
        reactor.callInThread(self.do_snapd_request, request)
        return NOT_DONE_YET
