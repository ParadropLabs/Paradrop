from paradrop.lib.config import configservice, uciutils
from paradrop.lib.utils import uci
from paradrop.lib.utils.output import out, logPrefix

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

def setOSFirewallRules(update):
    """
    Takes a list of tuples (config, opts) and saves it to the firewall config file.
    """
    changed = uciutils.setConfig(update.new, update.old,
            cacheKeys=['osFirewallRules'], filepath=uci.FIREWALL_PATH)

    # If we didn't change anything, then return the function to reloadFirewall so we can save ourselves from that call
    if(not changed):
        return configservice.reloadFirewall

