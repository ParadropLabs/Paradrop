###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import socket, struct

def isIpValid(ipaddr):
    """Return True if Valid, otherwise False."""
    try:
        socket.inet_aton(ipaddr)
        return True
    except:
        return False
    
def isIpAvailable(ipaddr, chuteStor, name):
    """Make sure this IP address is available. 
       Checks the IP addresses of all zones on all other chutes,
        makes sure subnets are not the same."""
   
    #return True
    #TODO: Need to get this working for all types of chutes
    chList = chuteStor.getChuteList()
    
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            otherIPs = ch.getChuteIPs()
            #print("chute: %s other IPs: %s" % (ch, otherIPs))
            for o in otherIPs:
                if isSameSubnet(ipaddr, o):
                    return False 
    
    return True


def isWifiSSIDAvailable(ssid, chuteStor, name):
    """Make sure this SSID is available."""
    
    #TODO: Need to get this working for all types of chutes
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


def isWifiIntAvailable(radioid, numWifi, chuteStor, name):
    """Make sure that fewer than 7 wifi interfaces have been configured.
    Otherwise, the wireless card will fail."""
   
    #TODO: Need to get this working for all types of chutes
    # TODO - change this needs to be more accurate 
    chList = chuteStor.getChuteList()
    
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            #print("chute: %s num WIFIs: %s" % (ch, ch.getChuteNumWifiInts()))
            # This is a wireless interface, so increment
            if (radioid == ch.getRadioID()):
                numWifi += ch.getChuteNumWifiInts()
                # more than 8 wifi interfaces, so cannot allocate another
                if (numWifi > 8):    
                    return False
            
    return True

def areWanPortsAvailable(portRange, takenPorts, chuteStor, name):
    """Make sure that if we are forwarding a wan port, we have not already forwarded it."""
   
    chList = chuteStor.getChuteList()
    (startPort, endPort) = portRange
    
    # Check that ports are not taken by other chutes
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            
            # Two ranges cannot overlap
            for (o_start, o_end) in ch.trafficWANPorts:
                if (max(startPort, o_start) <= min(endPort, o_end)):
                    return False
           
    # Check ports from the same chute (passed in as arg)
    for (o_start, o_end) in takenPorts: 
        if (max(startPort, o_start) <= min(endPort, o_end)):
            return False
 
    return True

def isStaticIpAvailable(ipaddr, chuteStor, name):
    """Make sure this static IP address is available. 
       Checks the IP addresses of all zones on all other chutes,
        makes sure not equal."""
   
    #return True
    #TODO: Need to get this working for all types of chutes
    chList = chuteStor.getChuteList()
    
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            otherStaticIPs = ch.getChuteStaticIPs()
            #print("chute: %s other IPs: %s" % (ch, otherIPs))
            for o in otherStaticIPs:
                if (ipaddr == o):
                    return False 
    
    return True

def isStaMeshAvailable(chuteStor, name):
    """Make sure this sta/mesh is available. Only one per device because we attach to wan directly."""
    chList = chuteStor.getChuteList()
    
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            if (ch.isStaMode() or ch.isMeshMode()):
                return False 
    return True

def isStaMeshOnRadio(radioid, chuteStor, name):
    """If we are a wifi chute, we cannot have an sta on this channel."""
    chList = chuteStor.getChuteList()
    
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            if ((ch.isStaMode() or ch.isMeshMode()) and radioid == ch.getRadioID()):
                return True 
    return False

def checkPhyExists(radioid):
    """Check if this chute exists at all, a directory /sys/class/ieee80211/phyX must exist."""
    #DFW: used to be this, but when netns runs this doesn't exist, so we switched to using the debug sysfs '/sys/class/ieee80211/phy%d' % radioid
    return pdos.exists('/sys/kernel/debug/ieee80211/phy%d' % radioid)

def isWifiOnRadio(radioid, chuteStor, name):
    """Make sure this sta is available. Only one per device because we attach to wan directly."""
    chList = chuteStor.getChuteList()
    
    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            #print("chute: %s num WIFIs: %s" % (ch, ch.getChuteNumWifiInts()))
            # This is a wireless interface, so increment
            if (ch.getChuteNumWifiInts() > 0 and radioid == ch.getRadioID()):
                return True
    return False


def isRadioPassedthrough(radioid, chuteStor, name):
    """ Check if any chute has already passed through to a chute. """
    chList = chuteStor.getChuteList()

    for ch in chList:
        # Only look at other chutes
        if (name != ch.name):
            #print("chute: %s num WIFIs: %s" % (ch, ch.getChuteNumWifiInts()))
            # This is a wireless interface, so increment
            if (ch.isRadioPassedthrough() and radioid == ch.getRadioID()):
                return True
    return False

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
    except Exception as e:
        out.err('!! %s Unable to inc ipaddr: %s\n' % (logPrefix(), str(e)))
        return None

def maxIpaddr(ipaddr):
    """
        Takes a quad dot format IP address string and makes it the largest valid value still in the same subnet.

        Returns:
            Incremented quad dot IP string or None if error
    """
    try:
        val = struct.unpack("!I", socket.inet_aton(ipaddr))[0]
        nm = struct.unpack("!I", socket.inet_aton(settings.FC_NETMGMT_DEFAULT_NETMASK))[0]
        inc = struct.unpack("!I", socket.inet_aton("0.0.0.254"))[0]
        val &= nm
        val |= inc
        return socket.inet_ntoa(struct.pack('!I', val))
    except Exception as e:
        out.err('!! %s Unable to inc ipaddr: %s\n' % (logPrefix(), str(e)))
        return None

def getSubnet(ip1, sn1):
    try:
        val1 = struct.unpack("!I", socket.inet_aton(ip1))[0]
        nm = struct.unpack("!I", socket.inet_aton(sn1))[0]
        res = val1 & nm
        return socket.inet_ntoa(struct.pack('!I', res))
    except Exception as e:
        out.err('!! %s Unable to determine subnet: %s\n' % (logPrefix(), str(e)))
        return False

def isSameSubnet(ip1, ip2):
    try:
        val1 = struct.unpack("!I", socket.inet_aton(ip1))[0]
        val2 = struct.unpack("!I", socket.inet_aton(ip2))[0]
        nm = struct.unpack("!I", socket.inet_aton(settings.FC_NETMGMT_DEFAULT_NETMASK))[0]
        return (val1 & nm) == (val2 & nm)
    except Exception as e:
        out.err('!! %s Unable to determine subnet: %s\n' % (logPrefix(), str(e)))
        return False

def getChuteIntf(name, netIntfs):
    """This function takes a network interface name, and parses through the netIntfs
        object provided looking for a match, it returns name if none is found.
            Example:
                if 'lan' is the name, 'lan' will be returned.
                if 'wifilxc' is the name, 'c####wifilxc' will be returned.
        
        This function also deals with the usage of macro expansions:
            Example:
                If the developer defines a 'lan' interface for their chute, but they
                also have a rule that needs to point to the HOST lan interface, a conflict
                will occur.
                
                To solve this, the developer would specify the HOST lan with '@net.host.lan'
                and the chute lan with 'lan'.
    """
    # Try to expand the macro, if its None then there wasn't a macro,
    # in that case look for a match in netIntfs, but if there is a macro
    # then we expect it to be to define a HOST interface
    tmp = macromanager.expandMacro(name)
    if(tmp):
        return tmp
    # Otherwise look through rest of definitions
    for n in netIntfs:
        if(name == n['name']):
            return n['externalIntf']
    else:
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
    
    l = []
    for i in intfs:
        if(i['netType'] == 'wan'):
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
        if(i['netType'] == 'wan'):
            return i
    return None




#Unit test
if(__name__ == '__main__'):
    '''
    print(maxIpaddr('192.168.2.1'))
    print(incIpaddr('192.168.2.1', 1))
    print(incIpaddr('192.168.2.1', 10))
    print(incIpaddr('192.168.2.1', 100))
    print(incIpaddr('192.168.2.1', 200))
    print(incIpaddr('192.168.2.1', 300))
    print(isSameSubnet('192.168.2.1', '192.168.2.254'))
    print(isSameSubnet('192.168.3.1', '192.168.2.2'))
    print(isSameSubnet('12.168.3.1', '192.168.2.2'))
    '''
    print(getSubnet('12.168.3.1', '255.255.255.0'))
    print(getSubnet('12.168.80.1', '255.255.255.0'))
    print(getSubnet('12.168.80.255', '255.255.255.0'))
