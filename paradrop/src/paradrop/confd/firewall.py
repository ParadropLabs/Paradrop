from .base import ConfigObject, ConfigOption
from .command import Command


IPTABLES_WAIT = "5"


class ConfigDefaults(ConfigObject):
    typename = "defaults"

    options = [
        ConfigOption(name="input", default="ACCEPT"),
        ConfigOption(name="output", default="ACCEPT"),
        ConfigOption(name="forward", default="ACCEPT")
    ]

    def apply(self, allConfigs):
        commands = list()

        for path in ["input", "output", "forward"]:
            # Set the default policy.
            cmd = ["iptables", "--wait", IPTABLES_WAIT, "--table", "filter",
                    "--policy", path.upper(), getattr(self, path)]
            commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Create the delegate_X chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--new", "delegate_"+path]
            commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Jump to delegate_X chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--append", path.upper(),
                    "--jump", "delegate_"+path]
            commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Create the X_rule chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--new", path+"_rule"]
            commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Jump to X_rule chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--append", path.upper(),
                    "--jump", path+"_rule"]
            commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

        for path in ["prerouting", "postrouting"]:
            # Create the delegate_X chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--new", "delegate_"+path]
            commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Jump to delegate_X chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--append", path.upper(),
                    "--jump", "delegate_"+path]
            commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Create the X_rule chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--new", path+"_rule"]
            commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Jump to X_rule chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--append", path.upper(),
                    "--jump", path+"_rule"]
            commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

        return commands

    def revert(self, allConfigs):
        commands = list()

        for path in ["prerouting", "postrouting"]:
            # Jump to X_rule chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--delete", path.upper(),
                    "--jump", path+"_rule"]
            commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Create the X_rule chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--delete-chain", path+"_rule"]
            commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Jump to delegate_X chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--delete", path.upper(),
                    "--jump", "delegate_"+path]
            commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Create the delegate_X chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--delete-chain", "delegate_"+path]
            commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

        for path in ["input", "output", "forward"]:
            # Jump to X_rule chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--delete", path.upper(),
                    "--jump", path+"_rule"]
            commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Create the X_rule chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--delete-chain", path+"_rule"]
            commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Jump to paradrop_X chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--delete", path.upper(),
                    "--jump", "delegate_"+path]
            commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Create the paradrop_X chain.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--delete-chain", "delegate_"+path]
            commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            # Set the default policy.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--policy", path.upper(), "ACCEPT"]
            commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

        return commands

class ConfigZone(ConfigObject):
    typename = "zone"

    options = [
        ConfigOption(name="name", required=True),
        ConfigOption(name="network", type=list),
        ConfigOption(name="masq", type=bool, default=False),
        ConfigOption(name="conntrack", type=bool, default=False),
        ConfigOption(name="input", default="RETURN"),
        ConfigOption(name="forward", default="RETURN"),
        ConfigOption(name="output", default="RETURN")
    ]

    def __commands_iptables(self, allConfigs, action, prio):
        commands = list()

        for interface in self.interfaces:
            # Jump to zone input chain.
            chain = "zone_{}_input".format(self.name)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    action, "delegate_input",
                    "--in-interface", interface.config_ifname,
                    "--jump", chain]
            commands.append((prio, Command(cmd, self)))

            # If conntrack is enabled, allow incoming traffic that is
            # associated with allowed outgoing traffic.
            if self.conntrack:
                comment = "zone {} conntrack".format(self.name)
                cmd = ["iptables", "--wait", IPTABLES_WAIT,
                        "--table", "filter",
                        action, "input_rule",
                        "--in-interface", interface.config_ifname,
                        "--match", "state", "--state", "ESTABLISHED,RELATED",
                        "--match", "comment", "--comment", comment,
                        "--jump", "ACCEPT"]
                commands.append((prio, Command(cmd, self)))

            # Implement default policy for zone.
            comment = "zone {} default".format(self.name)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    action, "input_rule",
                    "--in-interface", interface.config_ifname,
                    "--match", "comment", "--comment", comment,
                    "--jump", self.input]
            commands.append((prio, Command(cmd, self)))

            # Jump to zone output chain.
            chain = "zone_{}_output".format(self.name)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    action, "delegate_output",
                    "--out-interface", interface.config_ifname,
                    "--jump", chain]
            commands.append((prio, Command(cmd, self)))

            # Implement default policy for zone.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    action, "output_rule",
                    "--out-interface", interface.config_ifname,
                    "--match", "comment", "--comment", comment,
                    "--jump", self.output]
            commands.append((prio, Command(cmd, self)))

            # Jump to zone forward chain.
            chain = "zone_{}_forward".format(self.name)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    action, "delegate_forward",
                    "--out-interface", interface.config_ifname,
                    "--jump", chain]
            commands.append((prio, Command(cmd, self)))

            # Implement default policy for zone.
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    action, "forward_rule",
                    "--out-interface", interface.config_ifname,
                    "--match", "comment", "--comment", comment,
                    "--jump", self.forward]
            commands.append((prio, Command(cmd, self)))

            # Jump to zone prerouting chain.
            chain = "zone_{}_prerouting".format(self.name)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    action, "delegate_prerouting",
                    "--in-interface", interface.config_ifname,
                    "--jump", chain]
            commands.append((prio, Command(cmd, self)))

            # Jump to zone postrouting chain.
            chain = "zone_{}_postrouting".format(self.name)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    action, "delegate_postrouting",
                    "--out-interface", interface.config_ifname,
                    "--jump", chain]
            commands.append((prio, Command(cmd, self)))

            if self.masq:
                comment = "zone {} masq".format(self.name)
                cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                       action, "POSTROUTING",
                       "--out-interface", interface.config_ifname,
                        "--match", "comment", "--comment", comment,
                       "--jump", "MASQUERADE"]
                commands.append((prio, Command(cmd, self)))

        return commands

    def apply(self, allConfigs):
        # Initialize the list of network:interface sections.
        self.interfaces = list()
        if self.network is not None:
            for networkName in self.network:
                # Look up the interface - may fail.
                interface = self.lookup(allConfigs, "network", "interface", networkName)
                self.interfaces.append(interface)

        commands = list()

        for path in ["input", "output", "forward"]:
            # Create the zone_NAME_X chain.
            chain = "zone_{}_{}".format(self.name, path)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--new", chain]
            commands.append((self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        for path in ["prerouting", "postrouting"]:
            # Create the zone_NAME_X chain.
            chain = "zone_{}_{}".format(self.name, path)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--new", chain]
            commands.append((self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        # Make sure the kernel module is loaded before we add any rules that
        # rely on it.
        if self.conntrack and not self.manager.conntrackLoaded:
            cmd = ["modprobe", "xt_conntrack"]
            commands.append((self.PRIO_IPTABLES_ZONE, Command(cmd, self)))
            self.manager.conntrackLoaded = True

        commands.extend(self.__commands_iptables(allConfigs, "--append",
                self.PRIO_IPTABLES_ZONE))

        if self.masq:
            self.manager.forwardingCount += 1
            if self.manager.forwardingCount == 1:
                cmd = ["sysctl", "--write",
                       "net.ipv4.conf.all.forwarding=1"]
                commands.append((self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        return commands

    def revert(self, allConfigs):
        commands = self.__commands_iptables(allConfigs, "--delete",
                -self.PRIO_IPTABLES_ZONE)

        if self.masq:
            self.manager.forwardingCount -= 1
            if self.manager.forwardingCount == 0:
                cmd = ["sysctl", "--write",
                       "net.ipv4.conf.all.forwarding=0"]
                commands.append((-self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        for path in ["input", "output", "forward"]:
            # Create the zone_NAME_X chain.
            chain = "zone_{}_{}".format(self.name, path)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "filter",
                    "--delete-chain", chain]
            commands.append((-self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        for path in ["prerouting", "postrouting"]:
            # Create the zone_NAME_X chain.
            chain = "zone_{}_{}".format(self.name, path)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                    "--delete-chain", chain]
            commands.append((self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        # Reset the list of network:interface sections.
        self.interfaces = list()

        return commands


class ConfigForwarding(ConfigObject):
    typename = "forwarding"

    options = [
        ConfigOption(name="src", required=True),
        ConfigOption(name="dest", required=True)
    ]

    def __commands(self, allConfigs, action, prio):
        commands = list()

        chain = "zone_{}_forward".format(self.dest)
        for src_iface in self.src_interfaces:
            comment = "{} to {}".format(self.src, self.dest)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,
                    "--table", "filter",
                    action, chain,
                    "--in-interface", src_iface.config_ifname,
                    "--match", "comment", "--comment", comment,
                    "--jump", "ACCEPT"]
            commands.append((prio, Command(cmd, self)))

        return commands

    def apply(self, allConfigs):
        self.src_zone = self.lookup(allConfigs, "firewall", "zone", self.src)

        # Initialize the list of network:interface sections.
        self.src_interfaces = list()
        if self.src_zone.network is not None:
            for networkName in self.src_zone.network:
                # Look up the interface - may fail.
                interface = self.lookup(allConfigs, "network", "interface", networkName)
                self.src_interfaces.append(interface)

        return self.__commands(allConfigs, "--append", self.PRIO_IPTABLES_RULE)

    def revert(self, allConfigs):
        return self.__commands(allConfigs, "--delete", -self.PRIO_IPTABLES_RULE)


class ConfigRedirect(ConfigObject):
    typename = "redirect"

    options = [
        ConfigOption(name="src"),
        ConfigOption(name="src_ip"),
        ConfigOption(name="src_dip"),
        ConfigOption(name="src_port"),
        ConfigOption(name="src_dport"),
        ConfigOption(name="proto", required=True),
        ConfigOption(name="dest"),
        ConfigOption(name="dest_ip"),
        ConfigOption(name="dest_port"),
        ConfigOption(name="target", default="DNAT")
    ]

    # Any of these values will be interpreted to mean that --proto and ports
    # should not be specified in the iptables rule.
    ANY_PROTO = set([None, "any", "none"])

    def __commands_dnat(self, allConfigs, action, prio):
        """
        Generate DNAT iptables rules.
        """
        commands = list()

        # Special cases:
        # None->skip protocol and port arguments,
        # tcpudp->[tcp, udp]
        if self.proto in self.ANY_PROTO:
            protocols = [None]
        elif self.proto == "tcpudp":
            protocols = ["tcp", "udp"]
        else:
            protocols = [self.proto]

        for proto in protocols:
            chain = "zone_{}_prerouting".format(self.src)
            cmd = ["iptables", "--wait", IPTABLES_WAIT,  "--table", "nat",
                   action, chain]

            if self.src_ip is not None:
                cmd.extend(["--source", self.src_ip])
            if self.src_dip is not None:
                cmd.extend(["--destination", self.src_dip])
            if proto is not None:
                cmd.extend(["--proto", proto])
                if self.src_port is not None:
                    cmd.extend(["--sport", self.src_port])
                if self.src_dport is not None:
                    cmd.extend(["--dport", self.src_dport])

            if self.dest_ip is not None:
                if self.dest_port is not None:
                    cmd.extend(["--jump", "DNAT", "--to-destination",
                                "{}:{}".format(
                                    self.dest_ip, self.dest_port)])
                else:
                    cmd.extend(["--jump", "DNAT", "--to-destination",
                               self.dest_ip])
            elif self.dest_port is not None:
                cmd.extend(["--jump", "REDIRECT", "--to-port",
                           self.dest_port])

            commands.append((prio, Command(cmd, self)))

        return commands

    def __commands_snat(self, allConfigs, action, prio):
        """
        Generate SNAT iptables rules.
        """
        commands = list()
        # TODO: implement SNAT rules
        return commands

    def apply(self, allConfigs):
        if self.target == "DNAT":
            commands = self.__commands_dnat(allConfigs, "--insert",
                    self.PRIO_CONFIG_IFACE)
        elif self.target == "SNAT":
            commands = self.__commands_snat(allConfigs, "--insert",
                    self.PRIO_CONFIG_IFACE)
        else:
            raise Exception("Unsupported target ({}) in config {} {}".format(
                self.target, self.typename, self.name))

        self.manager.forwardingCount += 1
        if self.manager.forwardingCount == 1:
            cmd = ["sysctl", "--write",
                   "net.ipv4.conf.all.forwarding=1"]
            commands.append((self.PRIO_CONFIG_IFACE, Command(cmd, self)))

        return commands

    def revert(self, allConfigs):
        if self.target == "DNAT":
            commands = self.__commands_dnat(allConfigs, "--delete",
                    -self.PRIO_CONFIG_IFACE)
        elif self.target == "SNAT":
            commands = self.__commands_snat(allConfigs, "--delete",
                    -self.PRIO_CONFIG_IFACE)
        else:
            commands = list()

        self.manager.forwardingCount -= 1
        if self.manager.forwardingCount == 0:
            cmd = ["sysctl", "--write",
                   "net.ipv4.conf.all.forwarding=0"]
            commands.append((-self.PRIO_CONFIG_IFACE, Command(cmd, self)))

        return commands


class ConfigRule(ConfigObject):
    typename = "rule"

    options = [
        ConfigOption(name="src"),
        ConfigOption(name="src_ip"),
        ConfigOption(name="src_port"),
        ConfigOption(name="src_mac"),
        ConfigOption(name="proto"),
        ConfigOption(name="dest"),
        ConfigOption(name="dest_ip"),
        ConfigOption(name="dest_port"),
        ConfigOption(name="target", required=True),
        ConfigOption(name="extra")
    ]

    def __commands(self, allConfigs, action, prio):
        commands = list()

        # Choose INPUT, FORWARD, or OUTPUT based on whether src and dest are
        # specified.
        if self.src and self.dest:
            chain = "zone_{}_forward".format(self.dest)
        elif self.src:
            chain = "zone_{}_input".format(self.src)
        elif self.dest:
            chain = "zone_{}_output".format(self.dest)
        else:
            # TODO: Is this right?
            chain = "input_rule"

        # Put together the common options for rules.
        cmd = ["iptables", "--wait", IPTABLES_WAIT,
                "--table", "filter",
                action, chain]

        # Source and destination IP address.
        if self.src_ip:
            cmd.extend(["--source", self.src_ip])
        if self.dest_ip:
            cmd.extend(["--destination", self.dest_ip])

        # Source and destination ports.
        if self.proto:
            cmd.extend(["--protocol", self.proto])
            if self.src_port:
                cmd.extend(["--sport", str(self.src_port)])
            if self.dest_port:
                cmd.extend(["--dport", str(self.dest_port)])

        # Source MAC address.
        if self.src_mac:
            cmd.extend(["--match", "mac", "--mac-source", self.src_mac])

        # Extra options such as "--match state --state ESTABLISHED,RELATED"
        if self.extra:
            cmd.append(self.extra)

        cmd.extend(["--jump", self.target])

        commands.append((prio, Command(cmd, self)))

        return commands

    def apply(self, allConfigs):
        return self.__commands(allConfigs, "--append", self.PRIO_IPTABLES_RULE)

    def revert(self, allConfigs):
        return self.__commands(allConfigs, "--delete", -self.PRIO_IPTABLES_RULE)
