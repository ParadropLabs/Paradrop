import httplib
import socket
import StringIO

import click


PARADROP_URN = "urn:schemas-upnp-org:service:Paradrop:1"


class SsdpResponse(httplib.HTTPResponse):
    def __init__(self, response_text, source):
        self.fp = StringIO.StringIO(response_text)
        self.debuglevel = 0
        self.strict = 0
        self.msg = None
        self._method = None
        self.source = source
        self.begin()


def perform_ssdp_discovery(service, timeout=5, retries=5, mx=3):
    # Standard multicast IP address and port for SSDP.
    group = ("239.255.255.250", 1900)

    message = "\r\n".join([
        "M-SEARCH * HTTP/1.1",
        "HOST: {0}:{1}",
        'MAN: "ssdp:discover"',
        "ST: {st}",
        "MX: {mx}"
    ]).format(*group, st=service, mx=mx)

    socket.setdefaulttimeout(timeout)

    sources = set()
    for _ in range(retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(message.format(*group, st=service, mx=mx), group)
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                response = SsdpResponse(data, addr)
                if addr[0] not in sources:
                    # We only want to return each node once.
                    sources.add(addr[0])
                    yield response
            except socket.timeout:
                break


@click.command('discover')
@click.pass_context
def root(ctx):
    """
    Discover Paradrop nodes on the network.
    """
    click.echo("Discovering...")
    for response in perform_ssdp_discovery(PARADROP_URN):
        click.echo("Response from {:16s}".format(response.source[0]))

        server = response.getheader("SERVER")
        if server is not None:
            click.echo("  {}".format(server))
