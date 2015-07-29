from paradrop.lib.config import configservice, uciutils
from paradrop.lib.utils import uci
from pdtools.lib.output import out
from pdtools.lib import pdutils


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
        config = {'type': 'dnsmasq', 'name': iface['externalIntf']}
        options = {
            'list': {'interface': [iface['externalIntf']]}
        }

        # Optional: developer can pass in a list of DNS nameservers to use
        # instead of the system default.
        if 'dns' in dhcp:
            options['noresolv'] = '1'
            options['list'] = {'server': dhcp['dns']}

        dhcpSettings.append((config, options))

        config = {'type': 'dhcp', 'name': iface['externalIntf']}
        options = {
            'interface': iface['externalIntf'],
            'start': dhcp['start'],
            'limit': dhcp['limit'],
            'leasetime': dhcp['lease'],

            # This last one tells clients that the router is the interface
            # inside the chute not the one in the host.
            'dhcp_option': "option:router,{}".format(iface['internalIpaddr'])
        }

        dhcpSettings.append((config, options))

    update.new.setCache('virtDHCPSettings', dhcpSettings)


def setVirtDHCPSettings(update):
    """
    Takes a list of tuples (config, opts) and saves it to the dhcp config file.
    """
    changed = uciutils.setConfig(update.new, update.old,
                                 cacheKeys=['virtDHCPSettings'],
                                 filepath=uci.getSystemPath("dhcp"))

    # If we didn't change anything, then return the function to reloadDHCP so
    # we can save ourselves from that call.
    if not changed:
        return configservice.reloadDHCP
