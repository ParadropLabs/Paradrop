import netifaces
import ipaddress
import six

from builtins import str

from paradrop.base.output import out
from paradrop.base import constants, pdutils, settings
from paradrop.lib.utils import datastruct, uci

from . import uciutils

# TODO: Instead of being a constant, look at device capabilities.
MAX_AP_INTERFACES = 8

# We use a 4-digit hex string, which gives us this maximum.
MAX_INTERFACE_NUMBERS = 65536

# Size of subnets to assign to chutes.
SUBNET_SIZE = 24

# Extra Wi-Fi interface options that we will pass on directly to confd.
# Deprecated: move to 'options' object after 1.0 release.
IFACE_EXTRA_OPTIONS = set([
    "auth_server", "auth_secret", "acct_server", "acct_secret", "acct_interval"
])


def reclaimNetworkResources(chute):
    """
    Reclaim network resources for a previously running chute.

    This function only applies to the special case in which pd starts up and
    loads a list of chutes that were running.  This function marks their IP
    addresses and interface names as taken so that new chutes will not use the
    same values.
    """
    pass


def split_interface_type(itype):
    words = itype.split("-")
    if len(words) == 1:
        return words[0], None
    else:
        return tuple(words)


def getWifiKeySettings(cfg, iface):
    """
    Read encryption settings from cfg and transfer them to iface.
    """
    # If 'key' is present, but 'encryption' is not, then default to
    # psk2.  If 'key' is not present, and 'encryption' is psk or psk2,
    # then we have an error.
    iface['encryption'] = "none"
    if 'key' in cfg:
        iface['key'] = cfg['key']
        iface['encryption'] = 'psk2'  # default to psk2
    if 'encryption' in cfg:
        iface['encryption'] = cfg['encryption']
        if cfg['encryption'].startswith('psk') and 'key' not in cfg:
            out.warn("Key field must be defined "
                     "when encryption is enabled.")
            raise Exception("No key field defined for WiFi encryption")


def select_chute_subnet_pool(host_config):
    """
    Select IP subnet to use as pool for chutes.

    Behavior depends on whether a static subnet is configured or auto
    configuration is requested. If the chuteSubnetPool option is set to 'auto',
    then we check the WAN interface address and choose either 10.128.0.0/9 or
    192.168.128.0/17 to avoid conflict.  Otherwise, we used the specified
    subnet.
    """
    pool = datastruct.getValue(host_config, "system.chuteSubnetPool", 'auto')
    wan_ifname = datastruct.getValue(host_config, 'wan.interface', 'eth0')

    if pool == 'auto':
        addresses = netifaces.ifaddresses(wan_ifname)
        ipv4_addrs = addresses.get(netifaces.AF_INET, [])

        if any(x['addr'].startswith("10.") for x in ipv4_addrs):
            return "192.168.128.0/17"
        else:
            return "10.128.0.0/9"

    else:
        return pool


def chooseSubnet(update, cfg, iface):
    reservations = update.cache_get('subnetReservations')

    # Check if the chute configuration requests a specific network.
    #
    # TODO: Implement a mode where a chute can request a preferred network, but
    # do not fail if it is unavailable.
    requested = cfg.get('ipv4_network', None)
    if requested is not None:
        network = ipaddress.ip_network(str(requested))
        if network in reservations:
            raise Exception(
                "Could not assign network {}, network already in use".format(
                    requested))
        else:
            reservations.add(network)
            return network

    # Get subnet configuration settings from host configuration.
    host_config = update.cache_get('hostConfig')
    network_pool = select_chute_subnet_pool(host_config)
    prefix_size = datastruct.getValue(host_config, "system.chutePrefixSize",
                                      SUBNET_SIZE)

    network = ipaddress.ip_network(str(network_pool))
    if prefix_size < network.prefixlen:
        raise Exception(
            "Router misconfigured: prefix size {} is invalid for network {}".
            format(prefix_size, network))

    subnets = network.subnets(new_prefix=prefix_size)
    for subnet in subnets:
        if subnet not in reservations:
            reservations.add(subnet)
            return subnet

    raise Exception("Could not find an available subnet")


def chooseExternalIntf(update, iface):
    if iface['type'] == "wifi-ap":
        # Generate initial portion (prefix) of interface name.
        #
        # NOTE: We add a "v" in front of the interface name to avoid triggering
        # the udev persistent net naming rules, which are hard-coded to certain
        # typical strings such as "eth*" and "wlan*" but not "veth*" or
        # "vwlan*".  We do NOT want udev renaming our virtual interfaces.
        prefix = "vwlan"

        # This name should be unique on the system, so the hash is very unlikely to
        # collide with anything.  It still can collide, but this will be our first
        # choice for an interface number.
        name = "{}:{}".format(update.new.name, iface['internalIntf'])
        base = hash(name)

        reservations = update.cache_get('interfaceReservations')

        for i in range(MAX_INTERFACE_NUMBERS):
            number = (base + i) % MAX_INTERFACE_NUMBERS
            intf = "{}{:04x}".format(prefix, number)
            if intf not in reservations:
                reservations.add(intf)
                return intf

        raise Exception("Could not find an available interface name")

    else:
        # For monitor and managed mode, use the existing primary interface.
        devices = update.cache_get('networkDevicesByName')
        if iface['device'] not in devices:
            raise Exception("Could not find device {}".format(iface['device']))

        device = devices[iface['device']]
        if 'primary_interface' not in device:
            raise Exception("Primary interface for {} not detected".format(
                device['name']))

        return device['primary_interface']


def getInterfaceAddress(update, name, cfg, iface):
    """
    Dynamically select IP address for the chute interface.

    This function will use a subnet from the chute subnet pool and assign IP
    addresses to the external (in host) and internal (in chute) interfaces.

    The addresses are stored in the iface object.
    """
    # Claim a subnet for this interface from the pool.
    subnet = chooseSubnet(update, cfg, iface)

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
    iface['externalIpaddr'] = str(next(hosts))
    iface['internalIpaddr'] = str(next(hosts))

    # Generate the internal IP address with prefix length (x.x.x.x/y) for
    # convenience of other code that expect that format (e.g. pipework).
    iface['ipaddrWithPrefix'] = "{}/{}".format(iface['internalIpaddr'],
                                               subnet.prefixlen)


def getNetworkConfigWifi(update, name, cfg, iface):
    dtype, mode = split_interface_type(cfg['type'])

    # Later code still depends on the mode field.
    iface['mode'] = mode

    # Generate a name for the new interface in the host.
    iface['externalIntf'] = chooseExternalIntf(update, iface)
    if len(iface['externalIntf']) > constants.MAX_INTERFACE_NAME_LEN:
        out.warn("Interface name ({}) is too long\n".format(
            iface['externalIntf']))
        raise Exception("Interface name is too long")

    wireless = cfg.get("wireless", {})
    iface['wireless'] = wireless

    if iface['type'] in ["wifi-ap", "wifi-sta"]:
        # Check for required fields.
        res = pdutils.check(wireless, dict, ['ssid'])
        if res:
            out.warn('WiFi network interface definition {}\n'.format(res))
            raise Exception("Interface definition missing field(s)")

        iface['ssid'] = wireless['ssid']

    # Optional encryption settings
    getWifiKeySettings(wireless, iface)

    # Give a warning if the dhcp block is missing, since it is likely
    # that developers will want a DHCP server to go with their AP.
    if 'dhcp' not in cfg:
        out.warn("No dhcp block found for interface {}; "
                 "will not run a DHCP server".format(name))


def getNetworkConfigVlan(update, name, cfg, iface):
    res = pdutils.check(cfg, dict, ['vlan_id'])
    if res:
        raise Exception("Interface definition missing field(s)")

    # Generate a name for the new interface in the host.
    iface['externalIntf'] = "br-lan.{}".format(cfg['vlan_id'])

    # Prevent multiple chutes from using the same VLAN.
    reservations = update.cache_get('interfaceReservations')
    if iface['externalIntf'] in reservations:
        raise Exception("Interface {} already in use".format(
            iface['externalIntf']))
    reservations.add(iface['externalIntf'])


def getNetworkConfigLan(update, name, cfg, iface):
    # Claim a subnet for this interface from the pool.
    iface['externalIntf'] = iface['device']


def get_current_phy_conf(update, device_id):
    """
    Lookup current configuration for a network device.

    This includes information such as the Wi-Fi channel.

    Returns a dictionary, which may be empty if no configuration was found.
    """
    hostConfig = update.cache_get('hostConfig')

    for dev in hostConfig.get('wifi', []):
        if dev.get('id', None) == device_id:
            return dev

    return {}


def satisfies_requirements(obj, requirements):
    """
    Checks that an object satifies given requirements.

    Every key-value pair in the requirements object must be present in the
    target object for it to be considered satisfied.

    Returns True/False.
    """
    for key, value in six.iteritems(requirements):
        if key not in obj:
            return False
        if obj[key] != value:
            return False
    return True


def fulfillDeviceRequest(update, cfg, devices):
    """
    Find a physical device that matches the requested device type.

    Raises an exception if one cannot be found.
    """
    dtype, mode = split_interface_type(cfg['type'])

    # Get list of devices by requested type.
    devlist = devices.get(dtype, [])

    reservations = update.cache_get('deviceReservations')

    bestDevice = None
    bestScore = -1

    for device in devlist:
        dname = device['name']

        # If the configuration object includes a 'requests' object, then look
        # up configuration of the device and check additional constraints, e.g.
        # channel or hwmode.
        if 'requests' in cfg:
            phyconf = get_current_phy_conf(update, device['id'])
            if not satisfies_requirements(phyconf, cfg['requests']):
                continue

        # Monitor, station, and airshark mode interfaces require exclusive
        # access to the device.
        if dtype == "wifi" and mode in ["monitor", "sta", "airshark"]:
            if reservations[dname].count() > 0:
                continue

            # Choose the first one that matches.
            bestDevice = device
            break

        # AP mode interfaces can share a device, but not with monitor mode or
        # station mode.
        elif dtype == "wifi" and mode == "ap":
            if reservations[dname].count(mode="monitor") > 0:
                continue
            if reservations[dname].count(mode="sta") > 0:
                continue

            apcount = reservations[dname].count(mode="ap")

            # Avoid exceeding the max. number of AP interfaces.
            if apcount >= MAX_AP_INTERFACES:
                continue

            # Otherwise, prefer interfaces that have at least one AP already.
            # This preference leaves interfaces available for other purposes
            # (e.g. monitor mode).
            if apcount > bestScore:
                bestDevice = device
                bestScore = apcount

        else:
            # Handle other devices types, namely "lan".  Assume they require
            # exclusive access.
            if reservations[dname].count() > 0:
                continue
            else:
                bestDevice = device
                break

    if bestDevice is not None:
        out.info("Assign device {} for requested type {}".format(
            bestDevice['name'], dtype))
        reservations[bestDevice['name']].add(update.new.name, dtype, mode)
        return bestDevice

    raise Exception(
        "Could not satisfy requirement for device of type {}.".format(dtype))


def getExtraOptions(cfg):
    """
    Get dictionary of extra wifi-iface options that we are not interpreting but
    just passing on to pdconf.
    """
    # Using an 'options' object in the configuration is more extensible than
    # enumerating the possible extra options.
    options = cfg.get('options', {})

    # Deprecated: remove after 1.0 release.
    for key, value in six.iteritems(cfg):
        if key in IFACE_EXTRA_OPTIONS:
            options[key] = value

    return options


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
    update.cache_set('networkInterfaces', interfaces)

    # Deprecated: we set this value in the chute cache here because there is
    # still code that depends on reading this from the chute storage.  This can
    # be removed when the corresponding call to getCache is removed.
    update.new.setCache('networkInterfaces', interfaces)

    # Make sure we only assign interfaces to running chutes.
    if not update.new.isRunning():
        return None

    devices = update.cache_get('networkDevices')

    for service in update.new.get_services():
        for name, cfg in six.iteritems(service.interfaces):
            # Check for required fields.
            res = pdutils.check(cfg, dict, ['type'])
            if res:
                out.warn('Network interface definition {}\n'.format(res))
                raise Exception("Interface definition missing field(s)")

            iface = {
                'name': name,  # Name (not used?)
                'service': service.name,  # Service name
                'type': cfg['type'],  # Type (wan, lan, wifi)
                'internalIntf': cfg['intfName'],  # Interface name in chute
                'l3bridge': cfg.get('l3bridge', None)  # Optional
            }

            getInterfaceAddress(update, name, cfg, iface)

            if cfg['type'].startswith("wifi"):
                # Try to find a physical device of the requested type.
                #
                # Note: we try this first because it can fail, and then we will not try
                # to allocate any resources for it.
                device = fulfillDeviceRequest(update, cfg, devices)
                iface['device'] = device['name']
                iface['phy'] = device['phy']

                getNetworkConfigWifi(update, name, cfg, iface)

            elif cfg['type'] == "vlan":
                getNetworkConfigVlan(update, name, cfg, iface)

            elif cfg['type'] == "lan":
                device = fulfillDeviceRequest(update, cfg, devices)
                iface['device'] = device['name']

                getNetworkConfigLan(update, name, cfg, iface)

            else:
                raise Exception("Unsupported network type, {}".format(
                    cfg['type']))

            # Pass on DHCP configuration if it exists.
            if 'dhcp' in cfg:
                iface['dhcp'] = cfg['dhcp']

            # TODO: Refactor!  The problem here is that `cfg` contains a mixture of
            # fields, some that we will interpret and some that we will pass on to
            # pdconf.  The result is a lot of logic that tests and copies without
            # actually accomplishing much.
            iface['options'] = getExtraOptions(cfg)

            interfaces.append(iface)

    update.cache_set('networkInterfaces', interfaces)

    # Deprecated: we set this value in the chute cache here because there is
    # still code that depends on reading this from the chute storage.  This can
    # be removed when the corresponding call to getCache is removed.
    update.new.setCache('networkInterfaces', interfaces)


def abortNetworkConfig(update):
    """
    Release resources claimed by chute network configuration.
    """
    pass


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

    interfaces = update.cache_get('networkInterfaces')

    osNetwork = list()

    for iface in interfaces:
        config = {'type': 'interface', 'name': iface['externalIntf']}

        if iface['type'] == "wifi-monitor":
            if not settings.ALLOW_MONITOR_MODE:
                raise Exception("Monitor mode interfaces are disallowed by the system settings.")

            # Monitor mode is a special case - do not configure an IP address
            # for it.
            options = {'proto': 'none', 'ifname': iface['externalIntf']}

        else:
            # TODO: Check if configured IP addresses conflict with reservations
            # by chutes and fail a sethostconfig operation in that case.
            options = {
                'proto': 'static',
                'ipaddr': iface['externalIpaddr'],
                'netmask': iface['netmask'],
                'ifname': iface['externalIntf']
            }

        # Add to our OS Network
        osNetwork.append((config, options))

    update.cache_set('osNetworkConfig', osNetwork)


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

    uciutils.setConfig(
        update,
        cacheKeys=['osNetworkConfig'],
        filepath=uci.getSystemPath("network"))


def revert_os_network_config(update):
    uciutils.setConfig(
        update,
        cacheKeys=['osNetworkConfig'],
        filepath=uci.getSystemPath("network"))


def getL3BridgeConfig(update):
    """
    Creates configuration sections for layer 3 bridging.
    """
    interfaces = update.cache_get('networkInterfaces')

    parprouted = list()

    for iface in interfaces:
        l3bridge = iface.get('l3bridge', None)
        if l3bridge is None:
            continue

        config = {'type': 'bridge'}
        options = {'interfaces': [iface['externalIntf'], l3bridge]}
        parprouted.append((config, options))

    update.cache_set('parproutedConfig', parprouted)


def setL3BridgeConfig(update):
    """
    Apply configuration for layer 3 bridging.
    """
    uciutils.setConfig(
        update,
        cacheKeys=['parproutedConfig'],
        filepath=uci.getSystemPath("parprouted"))


def revert_l3_bridge_config(update):
    uciutils.setConfig(
        update,
        cacheKeys=['parproutedConfig'],
        filepath=uci.getSystemPath("parprouted"))
