import os

import six

from paradrop.base.output import out
from paradrop.base import pdutils
from paradrop.core.config import uciutils
from paradrop.lib.utils import uci


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

    interfaces = update.cache_get('networkInterfaces')
    if interfaces is None:
        return

    dhcpSettings = list()

    for iface in interfaces:
        # Only look at interfaces with DHCP server requested.
        if 'dhcp' not in iface:
            continue
        dhcp = iface['dhcp']

        # Construct a path for the lease file that will be visible inside the
        # chute.
        leasefile = os.path.join(
            update.cache_get('externalSystemDir'),
            "dnsmasq-{}.leases".format(iface['name'])
        )

        # NOTE: Having one dnsmasq section for each interface deviates from how
        # OpenWRT does things, where they assume a single instance of dnsmasq
        # will be handling all DHCP and DNS needs.
        config = {'type': 'dnsmasq'}
        options = {
            'leasefile': leasefile,
            'interface': [iface['externalIntf']]
        }

        # Optional: developer can pass in a list of DNS nameservers to use
        # instead of the system default.
        #
        # This path -> clients query our dnsmasq server; dnsmasq uses the
        # specified nameservers and caches the results.
        if DNSMASQ_CACHE_ENABLED and 'dns' in dhcp:
            options['noresolv'] = '1'
            options['server'] = dhcp['dns']

        # Disable authoritative mode if serving as a relay.
        relay = dhcp.get('relay', None)
        if relay is not None:
            options['authoritative'] = False

        dhcpSettings.append((config, options))

        # Check for fields that are required if not in relay mode.
        res = pdutils.check(dhcp, dict, ['lease', 'start', 'limit'])
        if relay is None and res:
            out.warn('DHCP server definition {}\n'.format(res))
            raise Exception("DHCP server definition missing field(s)")

        config = {'type': 'dhcp', 'name': iface['externalIntf']}
        options = {
            'interface': iface['externalIntf'],
            'start': dhcp.get('start', None),
            'limit': dhcp.get('limit', None),
            'leasetime': dhcp.get('lease', None),
            'dhcp_option': []
        }

        # This option tells clients that the router is the interface inside the
        # chute not the one in the host.
        options['dhcp_option'].append("option:router,{}".format(iface['internalIpaddr']))

        # Optional: developer can pass in a list of DNS nameservers to use
        # instead of the system default.
        #
        # This path -> clients receive the list of DNS servers and query them
        # directly.
        if not DNSMASQ_CACHE_ENABLED and 'dns' in dhcp:
            options['dhcp_option'].append(",".join(["option:dns-server"] + dhcp['dns']))

        # Interpret the optional DHCP relay configuration.
        # - string: interpret as the IP address of the relay server.
        # - list: interpret as list of strings to pass to dnsmasq (--dhcp-relay options).
        if isinstance(relay, six.string_types):
            # TODO: Set the optional third argument (interface) to the name of
            # the network interface on which we expect DHCP response. This
            # could be the WAN interface or it could be VPN interface.
            options['relay'] = ["{},{}".format(iface['externalIpaddr'], relay)]
        elif isinstance(relay, list):
            options['relay'] = relay

        dhcpSettings.append((config, options))

    update.cache_set('virtDHCPSettings', dhcpSettings)


def setVirtDHCPSettings(update):
    """
    Takes a list of tuples (config, opts) and saves it to the dhcp config file.
    """
    uciutils.setConfig(update,
            cacheKeys=['virtDHCPSettings'],
            filepath=uci.getSystemPath("dhcp"))


def revert_dhcp_settings(update):
    uciutils.setConfig(update,
            cacheKeys=['virtDHCPSettings'],
            filepath=uci.getSystemPath("dhcp"))
