import six

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


def compute_hfsc_params(classes, capacity):
    result = dict()

    sum_priority = 0
    sum_avgrate = 0
    sum_limitrate = 0

    # During the first pass, calculate the sums of rates and priorities and
    # determine which service curves are present for each class.
    for cid, cl in classes:
        params = {
            "has_rt": False,
            "has_ls": False,
            "has_ul": False,
            "has_bend": False
        }

        # The avgrate option adds real-time (rt) service curve.
        if cl.avgrate is not None:
            sum_avgrate += cl.avgrate
            params['has_rt'] = True

        # The priority option adds link share (ls) service curve.
        if cl.priority is not None:
            sum_priority += cl.priority
            params['has_ls'] = True

        if cl.limitrate is not None:
            sum_limitrate += cl.limitrate
            params['has_ul'] = True

        # Note: if the class has neither rt nor ls curves,
        # it will get no service (packets dropped).

        # The packetsize or packetdelay are not very intuitive names, but we
        # use them to set the duration of the first bend of the service curve.
        if (cl.packetsize is not None or cl.packetdelay is not None):
            params['has_bend'] = True

        result[cid] = params

    for cid, cl in classes:
        params = result[cid]

        if params['has_rt']:
            # In steady state, each class with a real-time curve gets at least
            # its allocated rate. The avgrate option is interpreted as a
            # percentage of the capacity.
            params['rt_m2'] = float(cl.avgrate) * capacity / 100.0

            if params['has_bend']:
                # The classes with real-time curves are allowed to temporarily
                # burst up to the full capacity.
                params['rt_m1'] = float(cl.avgrate) / sum_avgrate * capacity

                params['rt_d'] = cl.packetdelay
                if cl.packetsize is not None:
                    transfer_delay = float(8 * cl.packetsize) / params['rt_m1']
                    params['rt_d'] = max(params['rt_d'], transfer_delay)

        if params['has_ls']:
            # In steady state, each class with a link-share curve gets a
            # proportion of the capacity defined by its priority.
            params['ls_m2'] = float(cl.priority) * capacity / 100.0

            if params['has_bend']:
                # Allow temporary burst up to the full capacity.
                params['ls_m1'] = float(cl.priority) / sum_priority * capacity

                params['ls_d'] = cl.packetdelay
                if cl.packetsize is not None:
                    transfer_delay = float(8 * cl.packetsize) / params['ls_m1']
                    params['ls_d'] = max(params['ls_d'], transfer_delay)

        if params['has_ul']:
            # Set steady state upper limit from a percentage of the capacity.
            params['ul_m2'] = float(cl.limitrate) * capacity / 100.0

    return result


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

        # Store ifname mainly for the revert command.
        self.config_ifname = interface.config_ifname

        classes = []
        default_classid = None
        classgroup = self.lookup(allConfigs, "qos", "classgroup", self.classgroup)
        for class_name, class_id in six.iteritems(classgroup.class_id_map):
            if class_name == classgroup.default:
                default_classid = class_id

            traffic_class = self.lookup(allConfigs, "qos", "class", class_name)
            classes.append((class_id, traffic_class))

        cmd = ["tc", "qdisc", "add",
                "dev", self.config_ifname,
                "root", "handle", "1:",
                "hfsc"]
        if default_classid is not None:
            cmd.extend(["default", str(default_classid)])
        commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

        hfsc_params = compute_hfsc_params(classes, self.upload)
        for class_id, traffic_class in classes:
            full_class_id = "1:{}".format(class_id)
            params = hfsc_params[class_id]

            cmd = [
                "tc", "class", "add",
                "dev", self.config_ifname,
                "parent", "1:",
                "classid", full_class_id,
                "hfsc"
            ]

            if params['has_rt']:
                cmd.append("rt")
                if params['has_bend']:
                    cmd.extend(["m1", str(params['rt_m1']) + "kbit",
                                "d", str(params['rt_d']) + "ms"])
                cmd.extend(["m2", str(params['rt_m2']) + "kbit"])

            if params['has_ls']:
                cmd.append("ls")
                if params['has_bend']:
                    cmd.extend(["m1", str(params['ls_m1']) + "kbit",
                                "d", str(params['ls_d']) + "ms"])
                cmd.extend(["m2", str(params['ls_m2']) + "kbit"])

            if params['has_ul']:
                cmd.extend(["ul", "m2", str(params['ul_m2'])+"kbit"])

            commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

            # Add a fair queue to each class so that flows within the same
            # class receive fair treatment.
            cmd = [
                "tc", "qdisc", "add",
                "dev", self.config_ifname,
                "parent", full_class_id,
                "fq_codel", "noecn"
            ]
            commands.append((self.PRIO_CREATE_QDISC, Command(cmd, self)))

        return commands

    def revert(self, allConfigs):
        commands = list()

        if not self.enabled:
            return commands

        cmd = ["tc", "qdisc", "del", "dev", self.config_ifname, "root"]
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

        self.lookup(allConfigs, "qos", "class", self.target)

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
        ConfigOption(name="packetsize", type=int),
        ConfigOption(name="packetdelay", type=int),
        ConfigOption(name="maxsize", type=int),
        ConfigOption(name="avgrate", type=int),
        ConfigOption(name="limitrate", type=int),
        ConfigOption(name="priority", type=int)
    ]
