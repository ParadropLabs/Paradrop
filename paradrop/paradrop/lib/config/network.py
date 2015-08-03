import ipaddress
import itertools

from paradrop.lib import settings
from paradrop.lib.config import configservice, uciutils
from paradrop.lib.config.pool import NetworkPool, NamePool
from paradrop.lib.utils import addresses, uci
from pdtools.lib.output import out
from pdtools.lib import pdutils


MAX_INTERFACE_NAME_LEN = 15


# Pool of addresses available for chutes that request dynamic addressing.
networkPool = NetworkPool(settings.DYNAMIC_NETWORK_POOL)


# Pool of names for virtual interfaces.
interfaceNamePool = NamePool()


def getNetworkConfig(update):
    """
    For the Chute provided, return the dict object of a 100% filled out
    configuration set of network configuration. This would include determining
    what the IP addresses, interfaces names, etc...
    """

    # Notes:
    #
    # Fill in the gaps of knowledge between what the dev provided us in their
    # config and what would be required to add all the config changes to get
    # the chute working By the end of this function there should be a
    # cache:networkInterfaces key containing a list of dictionary objects for
    # each interface we will need to create, including netmasks IP addresses,
    # etc.. this is important to allow all other modules to know what the IP
    # addr is for this chute, etc..
    #
    # old code under lib.internal.chs.chutelxc same function name

    interfaces = list()

    if not hasattr(update.new, 'net'):
        update.new.setCache('networkInterfaces', interfaces)
        return None

    devices = update.new.getCache('networkDevices')
    devIters = {t: itertools.cycle(devices[t]) for t in devices.keys()}

    for name, cfg in update.new.net.iteritems():
        # First we must check the length of the name string, it cannot be
        # longer then 16-6 This is because the veth pair name for lxc cannot be
        # longer then 16, and we prepend "vc####" to that interface name
        if len(name) > 10:
            out.warn('The network interface name ({}) cannot be longer than '
                     '10 characters.\n'.format(name))
            raise Exception("Interface name too long")

        # Check for required fields.
        res = pdutils.check(cfg, dict, ['intfName', 'type'])
        if res:
            out.warn('Network interface definition {}\n'.format(res))
            raise Exception("Interface definition missing field(s)")

        # Claim a subnet for this interface from the pool.
        subnet = networkPool.next()
        hosts = subnet.hosts()

        # Generate internal (in the chute) and external (in the host)
        # addresses.
        #
        # Example:
        # subnet: 192.168.30.0/24
        # netmask: 255.255.255.0
        # external: 192.168.30.1
        # internal: 192.168.30.2
        netmask = str(subnet.netmask)
        externalIpaddr = str(hosts.next())
        internalIpaddr = str(hosts.next())

        # Generate the internal IP address with prefix length (x.x.x.x/y) for
        # convenience of other code that expect that format (e.g. pipework).
        ipaddrWithPrefix = "{}/{}".format(internalIpaddr, subnet.prefixlen)

        iface = {
            'name': name,                           # Name (not used?)
            'subnet': subnet,                       # Allocated subnet object
            'netType': cfg['type'],                 # Type (wan, lan, wifi)
            'internalIntf': cfg['intfName'],        # Interface name in chute
            'netmask': netmask,                     # Netmask in host and chute
            'externalIpaddr': externalIpaddr,       # IP address in host
            'internalIpaddr': internalIpaddr,       # IP address in chute
            'ipaddrWithPrefix': ipaddrWithPrefix    # Internal IP (x.x.x.x/y)
        }

        # Try to find a physical device of the requested type.
        try:
            device = devIters[cfg['type']].next()
            iface['device'] = device['name']
        except (KeyError, StopIteration):
            out.warn("Request for {} device cannot be fulfilled".
                     format(cfg['type']))
            raise Exception("Missing device(s) requested by chute")

        # Generate initial portion (prefix) of interface name.
        #
        # NOTE: We add a "v" in front of the interface name to avoid triggering
        # the udev persistent net naming rules, which are hard-coded to certain
        # typical strings such as "eth*" and "wlan*" but not "veth*" or
        # "vwlan*".  We do NOT want udev renaming our virtual interfaces.
        iface['extIntfPrefix'] = "v" + iface['device'] + "."

        # Generate a name for the new interface in the host.
        iface['externalIntf'] = interfaceNamePool.next(
            prefix=iface['extIntfPrefix'])
        if len(iface['externalIntf']) > MAX_INTERFACE_NAME_LEN:
            out.warn("Interface name ({}) is too long\n".
                     format(iface['externalIntf']))
            raise Exception("Interface name is too long")

        # Add extra fields for WiFi devices.
        if cfg['type'] == "wifi":
            # Check for required fields.
            res = pdutils.check(cfg, dict, ['ssid'])
            if res:
                out.warn('WiFi network interface definition {}\n'.format(res))
                raise Exception("Interface definition missing field(s)")

            iface['ssid'] = cfg['ssid']

            # Optional encryption settings
            #
            # If 'key' is present, but 'encryption' is not, then default to
            # psk2.  If 'key' is not present, and 'encryption' is not none,
            # then we have an error.
            if 'key' in cfg:
                iface['key'] = cfg['key']
                iface['encryption'] = 'psk2'  # default to psk2
            if 'encryption' in cfg:
                iface['encryption'] = cfg['encryption']
                if cfg['encryption'] != "none" and 'key' not in cfg:
                    out.warn("Key field must be defined "
                             "when encryption is enabled.")
                    raise Exception("No key field defined for WiFi encryption")

            # Give a warning if the dhcp block is missing, since it is likely
            # that developers will want a DHCP server to go with their AP.
            if 'dhcp' not in cfg:
                out.warn("No dhcp block found for interface {}; "
                         "will not run a DHCP server".format(name))

        # Pass on DHCP configuration if it exists.
        if 'dhcp' in cfg:
            iface['dhcp'] = cfg['dhcp']

        interfaces.append(iface)

    update.new.setCache('networkInterfaces', interfaces)


def getOSNetworkConfig(update):
    """
    Takes the network interface obj created by
    NetworkManager.getNetworkConfiguration and returns a properly formatted
    object to be passed to the OpenWrtConfig class.  The object returned is a
    list of tuples (config, options).
    """
    # Notes:
    #
    # Take the cache:networkInterfaces key and generate the UCI specific OS
    # config we need to inact the chute changes, should create a
    # cache:osNetworkConfig key
    #
    # old code under lib.internal.chs.chutelxc same function name

    # Make a dictionary of old interfaces, then remove them as we go
    # through the new interfaces.  Anything remaining should be freed.
    if update.old is not None:
        oldInterfaces = update.old.getCache('networkInterfaces')
        removedInterfaces = {iface['name']: iface for iface in oldInterfaces}
    else:
        removedInterfaces = dict()

    interfaces = update.new.getCache('networkInterfaces')

    osNetwork = list()

    for iface in interfaces:
        # A basic set of things must exist for all interfaces
        config = {'type': 'interface', 'name': iface['externalIntf']}

        # LXC network interfaces are always bridges
        options = {
            'type': "bridge",
            'proto': 'static',
            'ipaddr': iface['externalIpaddr'],
            'netmask': iface['netmask'],
            'ifname': iface['externalIntf']
        }

        # Add to our OS Network
        osNetwork.append((config, options))

        # This interface is still in use.
        if iface['name'] in removedInterfaces:
            del removedInterfaces[iface['name']]

    for iface in removedInterfaces.values():
        # Release the external interface name.
        interfaceNamePool.release(iface['externalIntf'],
                                  prefix=iface['extIntfPrefix'])

        # Release the subnet so another chute can use it.
        networkPool.release(iface['subnet'])

    update.new.setCache('osNetworkConfig', osNetwork)


def setOSNetworkConfig(update):
    """
    Takes a list of tuples (config, opts) and saves it to the network config
    file.
    """

    # Notes:
    #
    # Takes the config generated (cache:osNetworkConfig) and uses the UCI
    # module to actually push it to the disk
    #
    # old code under lib.internal.chs.chutelxc same function name

    changed = uciutils.setConfig(update.new, update.old,
                                 cacheKeys=['osNetworkConfig'],
                                 filepath=uci.getSystemPath("network"))

    # If we didn't change anything, then return the function to reloadNetwork
    # so we can save ourselves from that call
    if(not changed):
        return configservice.reloadNetwork


def getVirtNetworkConfig(update):
    out.warn('TODO implement me\n')
    # old code under lib.internal.chs.chutelxc same function name
    # Takes any network specific config and sets up the cache:virtNetworkConfig
    # this would be the place to put anything into HostConfig or the dockerfile
    # we need
