###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import socket
import struct

from paradrop.lib.utils import pdos


def isIpValid(ipaddr):
    """Return True if Valid, otherwise False."""
    try:
        socket.inet_aton(ipaddr)
        return True
    except:
        return False
    

def isIpAvailable(ipaddr, chuteStor, name):
    """
    Make sure this IP address is available. 

    Checks the IP addresses of all zones on all other chutes, makes sure
    subnets are not the same.
    """
    chList = chuteStor.getChuteList()
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            otherIPs = ch.getChuteIPs()
            if ipaddr in otherIPs:
                return False
    
    return True


def isWifiSSIDAvailable(ssid, chuteStor, name):
    """Make sure this SSID is available."""
    chList = chuteStor.getChuteList()
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            otherSSIDs = ch.getChuteSSIDs()    
            #print("chute: %s other SSIDs: %s" % (ch, otherSSIDs))
            for o in otherSSIDs:        
                if (o == ssid):
                    return False

    return True


def isStaticIpAvailable(ipaddr, chuteStor, name):
    """
    Make sure this static IP address is available. 

    Checks the IP addresses of all zones on all other chutes,
    makes sure not equal."""
    chList = chuteStor.getChuteList()
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            otherStaticIPs = ch.getChuteStaticIPs()
            if ipaddr in otherStaticIPs:
                return False 
    
    return True


def checkPhyExists(radioid):
    """Check if this chute exists at all, a directory /sys/class/ieee80211/phyX must exist."""
    #DFW: used to be this, but when netns runs this doesn't exist, so we switched to using the debug sysfs '/sys/class/ieee80211/phy%d' % radioid
    return pdos.exists('/sys/kernel/debug/ieee80211/phy%d' % radioid)


def incIpaddr(ipaddr, inc=1):
    """
        Takes a quad dot format IP address string and adds the @inc value to it by converting it to a number.

        Returns:
            Incremented quad dot IP string or None if error
    """
    try:
        val = struct.unpack("!I", socket.inet_aton(ipaddr))[0]
        val += inc
        return socket.inet_ntoa(struct.pack('!I', val))
    except Exception:
        return None


def maxIpaddr(ipaddr, netmask):
    """
        Takes a quad dot format IP address string and makes it the largest valid value still in the same subnet.

        Returns:
            Max quad dot IP string or None if error
    """
    try:
        val = struct.unpack("!I", socket.inet_aton(ipaddr))[0]
        nm = struct.unpack("!I", socket.inet_aton(netmask))[0]
        inc = struct.unpack("!I", socket.inet_aton("0.0.0.254"))[0]
        val &= nm
        val |= inc
        return socket.inet_ntoa(struct.pack('!I', val))
    except Exception:
        return None


def getSubnet(ipaddr, netmask):
    try:
        val1 = struct.unpack("!I", socket.inet_aton(ipaddr))[0]
        nm = struct.unpack("!I", socket.inet_aton(netmask))[0]
        res = val1 & nm
        return socket.inet_ntoa(struct.pack('!I', res))
    except Exception:
        return None


def getInternalIntfList(ch):
    """
        Takes a chute object and uses the key:networkInterfaces to return a list of the internal
        network interfaces that will exist in the chute (e.g., eth0, eth1, ...)

        Returns:
            A list of interface names
            None if networkInterfaces doesn't exist or there is an error
    """
    intfs = ch.getCache('networkInterfaces')
    if(not intfs):
        return None
    l = []
    for i in intfs:
        l.append(i['internalIntf'])

    return l


def getGatewayIntf(ch):
    """
        Looks at the key:networkInterfaces for the chute and determines what the gateway should be
        including the IP address and the internal interface name.

        Returns:
            A tuple (gatewayIP, gatewayInterface)
            None if networkInterfaces doesn't exist or there is an error
    """
    intfs = ch.getCache('networkInterfaces')
    if(not intfs):
        return (None, None)

    for i in intfs:
        if(i['type'] == 'wan'):
            return (i['externalIpaddr'], i['internalIntf'])

    return (None, None)


def getWANIntf(ch):
    """
        Looks at the key:networkInterfaces for the chute and finds the WAN interface.

        Returns:
            The dict from networkInterfaces
            None
    """
    intfs = ch.getCache('networkInterfaces')
    if(not intfs):
        return None
    
    for i in intfs:
        if(i['type'] == 'wan'):
            return i
    return None
