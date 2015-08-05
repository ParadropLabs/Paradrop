from paradrop.lib.config import configservice, uciutils
from paradrop.lib.utils import uci
from pdtools.lib.output import out
from pdtools.lib import pdutils


# Should dnsmasq be used to cache DNS lookup results or should clients send
# their queries directly to specified nameserver(s)?  This question only
# applies if the developer explicitly specified DNS nameservers.  Otherwise,
# dnsmasq acts as a cache and uses whatever nameserver(s) the host
# /etc/resolv.conf file specifies.
DNSMASQ_CACHE_ENABLED = True


def getVirtDHCPSettings(update):
    """
    Looks at the runtime rules the developer defined to see if they want a dhcp
    server.  If so it generates the data and stores it into the chute cache
    key:virtDHCPSettings.
    """

    interfaces = update.new.getCache('networkInterfaces')
    if interfaces is None:
        return

    dhcpSettings = list()

    for iface in interfaces:
        # Only look at interfaces with DHCP server requested.
        if 'dhcp' not in iface:
            continue
        dhcp = iface['dhcp']

        # Check for required fields.
        res = pdutils.check(dhcp, dict, ['lease', 'start', 'limit'])
        if(res):
            out.warn('DHCP server definition {}\n'.format(res))
            raise Exception("DHCP server definition missing field(s)")

        # NOTE: Having one dnsmasq section for each interface deviates from how
        # OpenWRT does things, where they assume a single instance of dnsmasq
        # will be handling all DHCP and DNS needs.
        config = {'type': 'dnsmasq'}
        options = {}
        uciutils.setList(options, 'interface', [iface['externalIntf']])

        # Optional: developer can pass in a list of DNS nameservers to use
        # instead of the system default.
        #
        # This path -> clients query our dnsmasq server; dnsmasq uses the
        # specified nameservers and caches the results.
        if DNSMASQ_CACHE_ENABLED and 'dns' in dhcp:
            options['noresolv'] = '1'
            uciutils.setList(options, 'server', dhcp['dns'])

        dhcpSettings.append((config, options))

        config = {'type': 'dhcp', 'name': iface['externalIntf']}
        options = {
            'interface': iface['externalIntf'],
            'start': dhcp['start'],
            'limit': dhcp['limit'],
            'leasetime': dhcp['lease'],
        }

        # This option tells clients that the router is the interface inside the
        # chute not the one in the host.
        uciutils.setList(options, 'dhcp_option', ["option:router,{}".format(
                                                    iface['internalIpaddr'])])

        # Optional: developer can pass in a list of DNS nameservers to use
        # instead of the system default.
        #
        # This path -> clients receive the list of DNS servers and query them
        # directly.
        if not DNSMASQ_CACHE_ENABLED and 'dns' in dhcp:
            uciutils.appendListItem(options, 'dhcp_option',
                    ",".join(["option:dns-server"] + dhcp['dns']))

        dhcpSettings.append((config, options))

    update.new.setCache('virtDHCPSettings', dhcpSettings)


def setVirtDHCPSettings(update):
    """
    Takes a list of tuples (config, opts) and saves it to the dhcp config file.
    """
    changed = uciutils.setConfig(update.new, update.old,
                                 cacheKeys=['virtDHCPSettings'],
                                 filepath=uci.getSystemPath("dhcp"))
