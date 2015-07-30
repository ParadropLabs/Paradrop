class Command(object):
    # Command priorities, lower numbers executed first.
    PRIO_CREATE_IFACE = 10
    PRIO_CONFIG_IFACE = 20
    PRIO_START_DAEMON = 30
    PRIO_ADD_IPTABLES = 40
    PRIO_DELETE_IFACE = 50

    def __init__(self, priority, command):
        self.priority = priority
        self.command = command
