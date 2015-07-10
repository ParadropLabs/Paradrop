
from paradrop.lib.config import configservice, uciutils
from paradrop.lib.utils import addresses, pdutils, uci
from paradrop.lib.utils.output import out, logPrefix

MAX_INTERFACE_NAME_LEN = 16

def getNetworkConfig(update):
    """
    For the Chute provided, return the dict object of a 100% filled out configuration set of network
    configuration. This would include determining what the IP addresses, interfaces names, etc...
    """

    # Notes:
    #
    # Fill in the gaps of knowledge between what the dev provided us in their config
    # and what would be required to add all the config changes to get the chute working
    # By the end of this function there should be a cache:networkInterfaces key containing
    # a list of dictionary objects for each interface we will need to create, including netmasks
    # IP addresses, etc.. this is important to allow all other modules to know what the IP addr is
    # for this chute, etc..
    #
    # old code under lib.internal.chs.chutelxc same function name

    interfaces = list()

    if(not hasattr(update, 'net')):
        return None
    for name, cfg in update.net.iteritems():
        # First we must check the length of the name string, it cannot be
        # longer then 16-6 This is because the veth pair name for lxc cannot be
        # longer then 16, and we prepend "vc####" to that interface name
        if(len(name) > 10):
            out.warn('** {} The network interface name ({}) cannot be longer than 10 characters.\n'.format(
                logPrefix(), name))
            raise Exception("Interface name too long")

        # Check for required fields.
        res = pdutils.check(cfg, dict, ['ipaddr', 'intfName', 'type', 'netmask'])
        if(res):
            out.warn('** {} Network interface definition {}\n'.format(logPrefix(), res))
            raise Exception("Interface definition missing field(s)")

        # verify that this chute can have the IP provided
        if(not addresses.isIpValid(cfg['ipaddr'])):
            out.warn('** {} IP address ({}) not valid for {}'.format(
                logPrefix(), cfg['ipaddr'], name))
            raise Exception("IP address not valid")

        # Verify that no other interfaces on other chutes are using this IP address
        if(not addresses.isIpAvailable(cfg['ipaddr'], update.chuteStor, update.new.name)):
            out.warn('** {} IP address ({}) requested by {} already in use'.format(
                logPrefix(), cfg['ipaddr'], name))
            raise Exception("IP address in use")

        iface = {
            'name': name,
            'netType': cfg['type'],
            'internalIntf': cfg['intfName'],
            'internalIpaddr': cfg['ipaddr'],
            'netmask': cfg['netmask']
        }

        # Setup the external interface info for this chute:
        externalIpaddr = addresses.incIpaddr(cfg['ipaddr'])
        iface['externalIpaddr'] = externalIpaddr

        # The external interface is defined above in the class docs
        prefixLen = MAX_INTERFACE_NAME_LEN - len(name) - 1
        externalIntf="{}.{}".format(update.new.name[0:prefixLen], name)
        iface['externalIntf'] = externalIntf

        interfaces.append(iface)

    update.new.setCache('networkInterfaces', interfaces)

def getOSNetworkConfig(update):
    """
    Takes the network interface obj created by NetworkManager.getNetworkConfiguration
    and returns a properly formatted object to be passed to the OpenWrtConfig class.
    The object returned is a list of tuples (config, options).
    """
    # Notes:
    #
    # Take the cache:networkInterfaces key and generate the UCI specific OS config we need
    # to inact the chute changes, should create a cache:osNetworkConfig key
    #
    # old code under lib.internal.chs.chutelxc same function name

    interfaces = update.new.getCache('networkInterfaces')

    osNetwork = list()

    if(interfaces is None):
        return None

    for iface in interfaces:
        # A basic set of things must exist for all interfaces
        config = {'type': 'interface', 'name': iface['externalIntf']}
 
        # LXC network interfaces are always bridges
        options = {
            'type': "bridge", 
            'proto': 'static', 
            'ipaddr': iface['externalIpaddr'], 
            'netmask': iface['netmask']
        }

        # Populate the veth that LXC will create when this chute starts
        options['list'] = {
            'ifname': [iface['externalIntf']]
        }

        # Add to our OS Network
        osNetwork.append((config, options))

    update.new.setCache('osNetworkConfig', osNetwork)

def setOSNetworkConfig(update):
    """
    Takes a list of tuples (config, opts) and saves it to the network config file.
    """

    # Notes:
    #
    # Takes the config generated (cache:osNetworkConfig) and uses the UCI module to actually push
    # it to the disk
    #
    # old code under lib.internal.chs.chutelxc same function name

    changed = uciutils.setConfig(update.new, update.old, 
            cacheKeys=['osNetworkConfig'], filepath=uci.NET_PATH)

    # If we didn't change anything, then return the function to reloadNetwork so we can save ourselves from that call
    if(not changed):
        return configservice.reloadNetwork

def getVirtNetworkConfig(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # old code under lib.internal.chs.chutelxc same function name
    # Takes any network specific config and sets up the cache:virtNetworkConfig
    # this would be the place to put anything into HostConfig or the dockerfile we need
