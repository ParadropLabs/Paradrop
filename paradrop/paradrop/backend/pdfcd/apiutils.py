####################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

'''
backend.pdfcd.apiutils.
Contains helper functions specific to the backend API code.
'''
import socket
import struct


def getIP(req):
    """
    Returns the str IP addr from the request.
    NOTE: This is required because when we use nginx servers
    it is used as a proxy, so the REAL IP addr is stored in a HTTP header
    called 'X-Real-IP', so we need to check for this first, otherwise the
    request.getClientIP() is always going to return 'localhost' to us.
    """
    ip = req.received_headers.get('X-Real-IP')
    if(ip is None):
        return req.getClientIP()
    else:
        return ip


def addressInNetwork(ipaddr, netTuple):
    """
        This function allows you to check if on IP belongs to a Network.
        Arguments:
            unpacked IP address (use unpackIPAddr())
            tuple of unpacked (addr, netmask) (use unpackIPAddrWithSlash())
        Returns:
            True if in network
            False otherwise
        """
    network, netmask = netTuple
    return (ipaddr & netmask) == (network & netmask)


def calcDottedNetmask(mask):
    """Returns quad dot format of IP address."""
    bits = 0
    for i in xrange(32 - mask, 32):
        bits |= (1 << i)
    return "%d.%d.%d.%d" % ((bits & 0xff000000) >> 24, (bits & 0xff0000) >> 16, (bits & 0xff00) >> 8, (bits & 0xff))


def unpackIPAddrWithSlash(net):
    """
        Unpacks the 'IP/bitmask' str.
        Returns a tuple of binary forms of both the ipaddr and netmask such that (ipaddr & netmask) will work.
    """
    # Take "0.0.0.0/16" and split into 2 components
    netaddr, bits = net.split('/')
    # Get the quad dot addr of netmask
    netmask = struct.unpack('=L', socket.inet_aton(calcDottedNetmask(int(bits))))[0]
    # Get the unpacked addr of the IP
    network = struct.unpack('=L', socket.inet_aton(netaddr))[0]
    return (network, netmask)


def unpackIPAddr(ip):
    """
        Unpacks the 'IP' str.
        Returns a binary form of the ipaddr such that (ipaddr & netmask) will work.
    """
    return struct.unpack('=L', socket.inet_aton(ip))[0]
