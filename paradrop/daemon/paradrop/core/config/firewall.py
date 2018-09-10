import fnmatch

from paradrop.base.output import out
from paradrop.lib.utils import uci

from . import uciutils


def findMatchingInterface(iface_name, interfaces):
    """
    Search an interface list for one matching a given name.

    iface_name can contain shell-style wildcards (* and ?).
    """
    for iface in interfaces:
        if fnmatch.fnmatch(iface['name'], iface_name):
            return iface
    return None


def getOSFirewallRules(update):
    """
    There is a set of default things that must exist just for the chute to function at all, generate those here.

    Stored in key: osFirewallRules
    """
    interfaces = update.cache_get('networkInterfaces')
    if interfaces is None:
        return None

    rules = []

    # Add a zone for each interface.
    for iface in interfaces:
        config = {'type': 'zone'}
        options = {
            'name': iface['externalIntf'],
            'conntrack': True,
            'input': 'REJECT',
            'forward': 'ACCEPT',
            'output': 'ACCEPT',
            'network': [iface['externalIntf']]
        }

        if iface['type'] == 'wan':
            options['masq'] = 1
        else:
            options['masq'] = 0

        # Add the zone section first.
        rules.append((config, options))

        # Then add a forwarding rule for wan type interfaces.
        if iface['type'] == 'wan':
            config = {'type': 'forwarding'}
            options = {
                'src': iface['externalIntf'],
                'dest': 'wan'
            }
            rules.append((config, options))

        # If we are running a DHCP server for the chute, we should allow DHCP
        # and DNS requests to the host.
        if 'dhcp' in iface:
            # Allow DNS requests.
            config = {'type': 'rule'}
            options = {
                'src': iface['externalIntf'],
                'proto': 'udp',
                'dest_port': 53,
                'target': 'ACCEPT'
            }
            rules.append((config, options))

            # Allow DHCP requests.
            config = {'type': 'rule'}
            options = {
                'src': iface['externalIntf'],
                'proto': 'udp',
                'dest_port': 67,
                'target': 'ACCEPT'
            }
            rules.append((config, options))

    update.cache_set('osFirewallRules', rules)


def getDeveloperFirewallRules(update):
    """
    Generate other firewall rules requested by the developer such as redirects.
    The object returned is a list of tuples (config, options).
    """
    interfaces = update.cache_get('networkInterfaces')
    if interfaces is None:
        return None

    rules = list()

    if hasattr(update.new, "firewall"):
        for rule in update.new.firewall:
            if rule['type'] == 'redirect':
                config = {'type': 'redirect'}
                options = {
                    'name': rule['name'],
                    'proto': 'tcpudp'
                }

                from_parts = rule['from'].strip().split(':')
                to_parts = rule['to'].strip().split(':')

                # Do not allow rules that do not pertain to the chute.
                if "@host.lan" in from_parts[0] and "@host.lan" in to_parts[0]:
                    raise Exception("Unable to add firewall rule - "
                                    "dst and src are both outside of chute")

                # From @host.lan means this is a DNAT rule (redirect to the chute).
                if from_parts[0] == "@host.lan":
                    options['target'] = "DNAT"

                    options['src'] = "wan"
                    if len(from_parts) > 1:
                        options['src_dport'] = from_parts[1]

                    # Find the interface specified in the rule, so we can get its
                    # IP address.
                    iface = findMatchingInterface(to_parts[0], interfaces)
                    if iface is None:
                        out.warn("No interface found with name {}\n".format(to_parts[0]))
                        raise Exception("Interface not found")

                    options['dest_ip'] = iface['externalIpaddr']
                    if len(to_parts) > 1:
                        options['dest_port'] = to_parts[1]

                # This is an SNAT rule (redirect from the chute to host network).
                elif to_parts[0] == "@host.lan":
                    options['target'] = "SNAT"

                    # TODO: Implement
                    out.warn("SNAT rules not supported yet")
                    raise Exception("SNAT rules not implemented")

                # Could be forwarding between chute interfaces?
                else:
                    out.warn("Other rules not supported yet")
                    raise Exception("Other rules not implemented")

                rules.append((config, options))

    update.cache_set('developerFirewallRules', rules)


def setOSFirewallRules(update):
    """
    Takes a list of tuples (config, opts) and saves it to the firewall config file.
    """
    uciutils.setConfig(update,
            cacheKeys=['osFirewallRules', 'developerFirewallRules'],
            filepath=uci.getSystemPath("firewall"))


def revert_os_firewall_rules(update):
    uciutils.setConfig(update,
            cacheKeys=['osFirewallRules', 'developerFirewallRules'],
            filepath=uci.getSystemPath("firewall"))
