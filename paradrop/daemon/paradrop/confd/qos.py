from .base import ConfigObject, ConfigOption
from .command import Command


# Map class names to priority band numbers (0 is maximum priority).
DEFAULT_CLASSES = {
    "BestEffort": 2,
    "Bulk": 3,
    "Interactive": 1,
    "IntBulk": 2,
    "Priority": 0
}


class ConfigInterface(ConfigObject):
    typename = "interface"

    options = [
        ConfigOption(name="enabled", type=bool, required=True),
        ConfigOption(name="classgroup"),
        ConfigOption(name="overhead", type=bool, default=False),
        ConfigOption(name="upload", type=int),
        ConfigOption(name="download", type=int)
    ]

    def apply(self, allConfigs):
        commands = list()

        if not self.enabled:
            return commands

        # Look up the interface section.
        interface = self.lookup(allConfigs, "network", "interface", self.name)

        # Create four priority bands.  The first one (band 0) is reserved for
        # explicitly prioritized traffic.  The remaining three are
        # automatically selected if the traffic sets TOS bits.
        cmd = ["tc", "qdisc", "add", "dev", interface.config_ifname, "root",
                "handle", "1:", "prio", "bands", "4", "priomap"]
        cmd.extend("2 3 3 3 2 3 1 1 2 2 2 2 2 2 2 2".split(" "))
        commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

        # Add fair queues to all of the bands.
        for i in range(4):
            classid = "1:{}".format(i+1)
            cmd = ["tc", "qdisc", "add", "dev", interface.config_ifname,
                    "parent", classid, "fq"]
            commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

        # Add a filter rule that will classify packets based on what container
        # they came from (cgroup).
        #
        # TODO: What should the prio argument be?  We get an "invalid argument"
        # error if it is 10.
        cmd = ["tc", "filter", "add", "dev", interface.config_ifname, "parent",
                "1:", "protocol", "ip", "prio", "1", "handle", "1:", "cgroup"]
        commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

        return commands

    def revert(self, allConfigs):
        commands = list()

        if not self.enabled:
            return commands

        # Look up the interface section.
        interface = self.lookup(allConfigs, "qos", "interface", self.name)

        cmd = ["tc", "qdisc", "del", "dev", interface.config_ifname, "root"]
        commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

        return commands


class ConfigClassify(ConfigObject):
    typename = "classify"

    options = [
        ConfigOption(name="target", required=True),
        ConfigOption(name="proto"),
        ConfigOption(name="srchost"),
        ConfigOption(name="dsthost"),
        ConfigOption(name="ports", type=int),
        ConfigOption(name="srcports", type=int),
        ConfigOption(name="dstports", type=int),
        ConfigOption(name="portrange", type=int),
        ConfigOption(name="pktsize", type=int),
        ConfigOption(name="tcpflags"),
        ConfigOption(name="mark"),
        ConfigOption(name="connbytes", type=int),
        ConfigOption(name="tos"),
        ConfigOption(name="dscp"),
        ConfigOption(name="direction")
    ]


class ConfigClassgroup(ConfigObject):
    typename = "classgroup"

    options = [
        ConfigOption(name="classes", required=True),
        ConfigOption(name="default", required=True)
    ]

    def setup(self):
        # Map names to integer ids.
        self.class_id_map = dict()
        names = self.classes.split(" ")
        for i in range(len(names)):
            self.class_id_map[names[i]] = i+1


class ConfigClass(ConfigObject):
    typename = "class"

    options = [
        ConfigOption(name="packetsize", type=int, required=True),
        ConfigOption(name="packetdelay", type=int, required=True),
        ConfigOption(name="maxsize", type=int, required=True),
        ConfigOption(name="avgrate", type=int, required=True),
        ConfigOption(name="limitrate", type=int, default=100),
        ConfigOption(name="maxsize", type=int, required=True),
        ConfigOption(name="priority", type=int, required=True)
    ]
