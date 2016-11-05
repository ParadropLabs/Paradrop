import ipaddress
import itertools

from paradrop.base.lib.output import out
from paradrop.base.lib import pdutils
from paradrop.lib import settings
from paradrop.lib.config import configservice, uciutils
from paradrop.lib.config.pool import NetworkPool, NumericPool
from paradrop.lib.utils import addresses, uci


MAX_INTERFACE_NAME_LEN = 15


# Pool of addresses available for chutes that request dynamic addressing.
networkPool = NetworkPool(settings.DYNAMIC_NETWORK_POOL)


# Pool of numbers for virtual interfaces.
interfaceNumberPool = NumericPool()


def getInterfaceDict(chute):
    """
    Return interfaces from a chute as a dict with interface names as the keys.
    Returns an empty dict if chute is None or it had no interfaces.
    """
    oldInterfaces = dict()
    if chute is not None:
        cachedInterfaces = chute.getCache('networkInterfaces')
        oldInterfaces = {iface['name']: iface for iface in cachedInterfaces}
    return oldInterfaces


def reclaimNetworkResources(chute):
    """
    Reclaim network resources for a previously running chute.

    This function only applies to the special case in which pd starts up and
    loads a list of chutes that were running.  This function marks their IP
    addresses and interface names as taken so that new chutes will not use the
    same values.
    """
    interfaces = chute.getCache('networkInterfaces')
    if interfaces is None:
        return
    for iface in interfaces:
        interfaceNumberPool.reserve(iface['extIntfNumber'])
        networkPool.reserve(iface['subnet'])


def getWifiKeySettings(cfg, iface):
    """
    Read encryption settings from cfg and transfer them to iface.
    """
    # If 'key' is present, but 'encryption' is not, then default to
    # psk2.  If 'key' is not present, and 'encryption' is not none,
    # then we have an error.
    iface['encryption'] = "none"
    if 'key' in cfg:
        iface['key'] = cfg['key']
        iface['encryption'] = 'psk2'  # default to psk2
    if 'encryption' in cfg:
        iface['encryption'] = cfg['encryption']
        if cfg['encryption'] != "none" and 'key' not in cfg:
            out.warn("Key field must be defined "
                     "when encryption is enabled.")
            raise Exception("No key field defined for WiFi encryption")


def getNetworkConfigWifi(update, name, cfg, iface):
    # Make a dictionary of old interfaces.  Any new interfaces that are
    # identical to an old one do not need to be changed.
    oldInterfaces = getInterfaceDict(update.old)
    if name in oldInterfaces:
        oldIface = oldInterfaces[iface['name']]
        subnet = oldIface['subnet']
        iface['extIntfNumber'] = oldIface['extIntfNumber']

    else:
        # Claim a subnet for this interface from the pool.
        subnet = networkPool.next()
        iface['extIntfNumber'] = interfaceNumberPool.next()

    # Generate internal (in the chute) and external (in the host)
    # addresses.
    #
    # Example:
    # subnet: 192.168.30.0/24
    # netmask: 255.255.255.0
    # external: 192.168.30.1
    # internal: 192.168.30.2
    hosts = subnet.hosts()
    iface['subnet'] = subnet
    iface['netmask'] = str(subnet.netmask)
    iface['externalIpaddr'] = str(hosts.next())
    iface['internalIpaddr'] = str(hosts.next())

    # Generate the internal IP address with prefix length (x.x.x.x/y) for
    # convenience of other code that expect that format (e.g. pipework).
    iface['ipaddrWithPrefix'] = "{}/{}".format(
            iface['internalIpaddr'], subnet.prefixlen)

    # Generate initial portion (prefix) of interface name.
    #
    # NOTE: We add a "v" in front of the interface name to avoid triggering
    # the udev persistent net naming rules, which are hard-coded to certain
    # typical strings such as "eth*" and "wlan*" but not "veth*" or
    # "vwlan*".  We do NOT want udev renaming our virtual interfaces.
    iface['extIntfPrefix'] = "v" + iface['device'] + "."

    # Generate a name for the new interface in the host.
    iface['externalIntf'] = "{}{:04x}".format(
        iface['extIntfPrefix'], iface['extIntfNumber'])
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
        getWifiKeySettings(cfg, iface)

        # Give a warning if the dhcp block is missing, since it is likely
        # that developers will want a DHCP server to go with their AP.
        if 'dhcp' not in cfg:
            out.warn("No dhcp block found for interface {}; "
                     "will not run a DHCP server".format(name))


def getNetworkConfig(update):
    """
    For the Chute provided, return the dict object of a 100% filled out
    configuration set of network configuration. This would include determining
    what the IP addresses, interfaces names, etc...

    Store configuration in networkInterfaces cache entry.
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

    # Put the list in the cache now (shared reference), so that if we fail out
    # of this function after partial completion, the abort function can take
    # care of what made it into the list.
    update.new.setCache('networkInterfaces', interfaces)
    if not hasattr(update.new, 'net'):
        return None

    # Make a dictionary of old interfaces.  Any new interfaces that are
    # identical to an old one do not need to be changed.
    oldInterfaces = getInterfaceDict(update.old)

    devices = update.new.getCache('networkDevices')
    devIters = {t: itertools.cycle(devices[t]) for t in devices.keys()}

    for name, cfg in update.new.net.iteritems():
        # Check for required fields.
        res = pdutils.check(cfg, dict, ['intfName', 'type'])
        if res:
            out.warn('Network interface definition {}\n'.format(res))
            raise Exception("Interface definition missing field(s)")

        iface = {
            'name': name,                           # Name (not used?)
            'netType': cfg['type'],                 # Type (wan, lan, wifi)
            'internalIntf': cfg['intfName']         # Interface name in chute
        }

        oldIface = oldInterfaces.get(name, None)
        if oldIface is None or oldIface['netType'] != iface['netType']:
            # Try to find a physical device of the requested type.
            #
            # Note: we try this first because it can fail, and then we will not try
            # to allocate any resources for it.
            try:
                device = devIters[cfg['type']].next()
                iface['device'] = device['name']
            except (KeyError, StopIteration):
                out.warn("Request for {} device cannot be fulfilled".
                         format(cfg['type']))
                raise Exception("Missing device(s) requested by chute")
        else:
            iface['device'] = oldIface['device']

        if cfg['type'] == "wifi":
            getNetworkConfigWifi(update, name, cfg, iface)

        # Pass on DHCP configuration if it exists.
        if 'dhcp' in cfg:
            iface['dhcp'] = cfg['dhcp']

        interfaces.append(iface)

    update.new.setCache('networkInterfaces', interfaces)


def abortNetworkConfig(update):
    """
    Release resources claimed by chute network configuration.
    """
    oldInterfaces = getInterfaceDict(update.old)

    # Any interfaces in the cache need to go down, so we will release the
    # interface number and subnet that were allocated to them.
    interfaces = update.new.getCache('networkInterfaces')
    for iface in interfaces:
        # Only release newly allocated resources.  If update.old exists,
        # we will be restoring to its state.
        if iface['name'] not in oldInterfaces:
            interfaceNumberPool.release(iface['extIntfNumber'], strict=False)
            networkPool.release(iface['subnet'], strict=False)


def getOSNetworkConfig(update):
    """
    Takes the network interface obj created by
    NetworkManager.getNetworkConfiguration and returns a properly formatted
    object to be passed to the UCIConfig class.  The object returned is a
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
    removedInterfaces = getInterfaceDict(update.old)

    interfaces = update.new.getCache('networkInterfaces')

    osNetwork = list()

    for iface in interfaces:
        # A basic set of things must exist for all interfaces
        config = {'type': 'interface', 'name': iface['externalIntf']}

        options = {
            'proto': 'static',
            'ipaddr': iface['externalIpaddr'],
            'netmask': iface['netmask'],
            'ifname': iface['externalIntf']
        }

        # Add to our OS Network
        osNetwork.append((config, options))

        # This interface is still in use, so take it out of the remove set.
        if iface['name'] in removedInterfaces:
            del removedInterfaces[iface['name']]

    for iface in removedInterfaces.values():
        # Release the external interface name.
        interfaceNumberPool.release(iface['extIntfNumber'], strict=False)

        # Release the subnet so another chute can use it.
        networkPool.release(iface['subnet'], strict=False)

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


def getVirtNetworkConfig(update):
    out.warn('TODO implement me\n')
    # old code under lib.internal.chs.chutelxc same function name
    # Takes any network specific config and sets up the cache:virtNetworkConfig
    # this would be the place to put anything into HostConfig or the dockerfile
    # we need
