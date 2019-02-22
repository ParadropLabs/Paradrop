import ipaddress

from builtins import str
from http.server import BaseHTTPRequestHandler

import six

from twisted.internet.protocol import DatagramProtocol

from paradrop.base import settings
from paradrop.core.system import system_info


SSDP_ADDR = "239.255.255.250"

PARADROP_URN = "urn:schemas-upnp-org:service:Paradrop:1"


# Warning: SSDP can be used for traffic amplification attacks.
# See this for example: https://blog.cloudflare.com/ssdp-100gbps/
# We do not want Paradrop to be used for DoS attacks, so here are
# a couple of ways to guard against malicious behavior.
#
# 1. Configure iptables to block UDP port 1900 on the WAN interface.
#    This is up to the device owner to configure properly.
# 2. Only send responses to requests that came from private addresses,
#    as these should be LAN devices. This approach is implemented here.


class SsdpRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = six.StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = None
        self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


class SsdpResponder(DatagramProtocol):
    def startProtocol(self):
        self.transport.joinGroup(SSDP_ADDR)

    def datagramReceived(self, datagram, address):
        request = SsdpRequest(datagram)
        addr = ipaddress.ip_address(str(address[0]))

        # Since we really only need to support queries from clients based on
        # pdtools, we can be choosy about what requests we will respond to.
        #
        # 1. Only reply to M-SEARCH requests.
        # 2. The search target (ST) must match our URN or one of the common
        #    wildcard targets.
        # 3. The recipient MUST be a private IP address.
        if not request.error_code and \
                request.command == "M-SEARCH" and \
                request.path == "*" and \
                request.headers['ST'] in ["ssdp:all", "upnp:rootdevice", PARADROP_URN] and \
                request.headers['MAN'] == '"ssdp:discover"' and \
                addr.is_private:
            os_ver = system_info.getOSVersion()
            pd_ver = system_info.getPackageVersion("paradrop")

            message = "\r\n".join([
                "HTTP/1.1 200 OK",
                "CACHE-CONTROL: max-age=60",
                "LOCATION: http://{domain}",
                "SERVER: OS/{os_ver} UPnP/1.1 Paradrop/{pd_ver}",
                "ST: {urn}"
            ]).format(domain=settings.LOCAL_DOMAIN, os_ver=os_ver,
                    pd_ver=pd_ver, urn=PARADROP_URN)

            self.transport.write(message, address)

    def stop(self):
        self.ssdp.leaveGroup(SSDP_ADDR)
        self.ssdp.stopListening()
