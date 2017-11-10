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
        ConfigOption(name="classgroup", default="Default"),
        ConfigOption(name="overhead", type=bool, default=True),
        ConfigOption(name="upload", type=int, default=4096),
        ConfigOption(name="download", type=int, default=512)
    ]

    def apply(self, allConfigs):
        commands = list()

        if not self.enabled:
            return commands

        # Look up the interface section.
        interface = self.lookup(allConfigs, "network", "interface", self.name)

        classes = []
        default_classid = None
        classgroup = self.lookup(allConfigs, "qos", "classgroup", self.classgroup)
        for class_name, class_id in classgroup.class_id_map.iteritems():
            if class_name == classgroup.default:
                default_classid = class_id

            traffic_class = self.lookup(allConfigs, "qos", "class", class_name)
            classes.append((class_id, traffic_class))

        cmd = ["tc", "qdisc", "add",
                "dev", interface.config_ifname,
                "root", "handle", "1:",
                "hfsc"]
        if default_classid is not None:
            cmd.extend(["default", str(default_classid)])
        commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

        for class_id, traffic_class in classes:
            full_class_id = "1:{}".format(class_id)

            sum_avgrate = sum(x[1].avgrate for x in classes)
            rt_m1 = float(traffic_class.avgrate) / sum_avgrate * self.upload
            rt_m2 = float(traffic_class.avgrate) * self.upload / 100.0
            ls_m1 = rt_m1

            # packetsize in bytes
            # packetdelay in ms
            # bits / kbps results in a delay specified in ms
            transfer_delay = float(8 * traffic_class.packetsize) / self.upload
            rt_d = max(traffic_class.packetdelay, transfer_delay)
            ls_d = rt_d

            sum_priority = sum(x[1].priority for x in classes)
            ls_m2 = float(traffic_class.priority) / sum_priority * self.upload

            ul_rate = float(traffic_class.limitrate) * self.upload / 100

            cmd = [
                "tc", "class", "add",
                "dev", interface.config_ifname,
                "parent", "1:",
                "classid", full_class_id,
                "hfsc",
                "rt", "m1", str(rt_m1)+"kbit", "d", str(rt_d)+"ms", "m2", str(rt_m2)+"kbit",
                "ls", "m1", str(ls_m1)+"kbit", "d", str(ls_d)+"ms", "m2", str(ls_m2)+"kbit",
                "ul", "m2", str(ul_rate)+"kbit"
            ]
            commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

            # Add a fair queue to each class so that flows within the same
            # class receive fair treatment.
            cmd = [
                "tc", "qdisc", "add",
                "dev", interface.config_ifname,
                "parent", full_class_id,
                "fq"
            ]
            commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

        return commands

    def revert(self, allConfigs):
        commands = list()

        if not self.enabled:
            return commands

        # Look up the interface section.
        interface = self.lookup(allConfigs, "qos", "interface", self.name)

        cmd = ["tc", "qdisc", "del", "dev", interface.config_ifname, "root"]
        commands.append((-self.PRIO_CREATE_QDISC, Command(cmd, self)))

        return commands


class ConfigClassify(ConfigObject):
    typename = "classify"

    options = [
        ConfigOption(name="target", required=True),
        ConfigOption(name="proto"),
        ConfigOption(name="srchost"),
        ConfigOption(name="dsthost"),
        ConfigOption(name="ports"),
        ConfigOption(name="srcports"),
        ConfigOption(name="dstports"),
        ConfigOption(name="portrange"),
        ConfigOption(name="pktsize"),
        ConfigOption(name="tcpflags"),
        ConfigOption(name="mark"),
        ConfigOption(name="connbytes"),
        ConfigOption(name="tos"),
        ConfigOption(name="dscp"),
        ConfigOption(name="direction")
    ]

    def make_iptables_cmd(self, action, ifname, class_id):
        cmd = [
            "iptables",
            "--wait", "5",
            "--table", "mangle",
            action, "POSTROUTING",
            "--out-interface", ifname
        ]

        if self.proto is not None:
            cmd.extend(["--protocol", self.proto])

        if self.srchost is not None:
            cmd.extend(["--source", self.srchost])
        if self.dsthost is not None:
            cmd.extend(["--destination", self.dsthost])

        if self.ports is not None:
            cmd.extend(["--match", "multiport", "--ports", self.ports])
        if self.srcports is not None:
            cmd.extend(["--match", "multiport", "--source-ports", self.srcports])
        if self.dstports is not None:
            cmd.extend(["--match", "multiport", "--destination-ports", self.dstports])
        if self.portrange is not None:
            cmd.extend(["--match", "multiport", "--ports", self.portrange])

        if self.pktsize is not None:
            cmd.extend(["--match", "connbytes", "--connbytes", self.pktsize])
        if self.tcpflags is not None:
            cmd.extend(["--protocol", "tcp", "--tcp-flags", self.tcpflags])
        if self.mark is not None:
            cmd.extend(["--match", "mark", "--mark", self.mark])
        if self.connbytes is not None:
            cmd.extend(["--match", "connbytes", "--connbytes", self.connbytes])
        if self.tos is not None:
            cmd.extend(["--match", "tos", "--tos", self.tos])
        if self.dscp is not None:
            cmd.extend(["--match", "dscp", "--dscp-class", self.dscp])

        comment = "classify {}".format(self.target)
        cmd.extend([
            "--match", "comment", "--comment", comment,
            "--jump", "CLASSIFY",
            "--set-class", class_id
        ])

        return Command(cmd, self)

    def apply(self, allConfigs):
        self._created_rules = []
        commands = []

        target = self.lookup(allConfigs, "qos", "class", self.target)

        # Find all classgroup sections that contain the target class.
        for group in self.findByType(allConfigs, "qos", "classgroup"):
            class_id = group.get_class_id(self.target)
            if class_id is None:
                continue
            group.dependents.add(self)

            # Find all interfaces that use the classgroup.
            interface_query = {"classgroup": group.name}
            for interface in self.findByType(allConfigs, "qos", "interface",
                    where=interface_query):
                if not interface.enabled:
                    continue
                interface.dependents.add(self)

                network_interface = self.lookup(allConfigs, "network",
                        "interface", interface.name)

                full_class_id = "1:{}".format(class_id)

                args = (network_interface.config_ifname, full_class_id)
                cmd = self.make_iptables_cmd("--append", *args)

                # Save these arguments so that we can recreate the iptables
                # commands in the revert method.
                self._created_rules.append(args)

                commands.append((self.PRIO_IPTABLES_RULE, cmd))

        return commands

    def revert(self, allConfigs):
        commands = []
        for args in self._created_rules:
            cmd = self.make_iptables_cmd("--delete", *args)
            commands.append((-self.PRIO_IPTABLES_RULE, cmd))
        return commands


class ConfigClassgroup(ConfigObject):
    typename = "classgroup"

    options = [
        ConfigOption(name="classes", required=True),
        ConfigOption(name="default", required=True)
    ]

    def get_class_id(self, class_name):
        """
        Get ID for a traffic class in this group.

        Returns None if the class is not a member of the group.
        """
        return self.class_id_map.get(class_name, None)

    def setup(self):
        # Map names to integer ids.
        self.class_id_map = dict()
        names = self.classes.split(" ")
        for i in range(len(names)):
            self.class_id_map[names[i]] = i+1


class ConfigClass(ConfigObject):
    typename = "class"

    options = [
        ConfigOption(name="packetsize", type=int, default=0),
        ConfigOption(name="packetdelay", type=int, default=0),
        ConfigOption(name="maxsize", type=int),
        ConfigOption(name="avgrate", type=int, required=True),
        ConfigOption(name="limitrate", type=int, default=100),
        ConfigOption(name="priority", type=int, required=True)
    ]
