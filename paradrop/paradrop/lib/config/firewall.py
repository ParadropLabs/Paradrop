import fnmatch

from paradrop.lib.config import configservice, uciutils
from paradrop.lib.utils import uci
from pdtools.lib.output import out


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
    interfaces = update.new.getCache('networkInterfaces')
    if interfaces is None:
        return None

    rules = []

    # Add a zone for each interface.
    for iface in interfaces:
        config = {'type': 'zone'}
        options = {
            'name': iface['externalIntf'],
            'input': 'ACCEPT',
            'forward': 'REJECT',
            'output': 'ACCEPT',
            'network': iface['externalIntf']
        }

        if iface['netType'] == 'wan':
            options['masq'] = 1
        else:
            options['masq'] = 0

        # Add the zone section first.
        rules.append((config, options))

        # Then add a forwarding rule for wan type interfaces.
        if iface['netType'] == 'wan':
            rules.append(({'type': 'forwarding'}, {'src': iface['externalIntf'], 'dest': 'wan'}))

    update.new.setCache('osFirewallRules', rules)


def getDeveloperFirewallRules(update):
    """
    Generate other firewall rules requested by the developer such as redirects.
    The object returned is a list of tuples (config, options).
    """
    interfaces = update.new.getCache('networkInterfaces')
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

    update.new.setCache('developerFirewallRules', rules)


def setOSFirewallRules(update):
    """
    Takes a list of tuples (config, opts) and saves it to the firewall config file.
    """
    changed = uciutils.setConfig(update.new, update.old,
                                 cacheKeys=['osFirewallRules', 'developerFirewallRules'],
                                 filepath=uci.getSystemPath("firewall"))
