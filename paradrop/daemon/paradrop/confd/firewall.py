import ipaddress

from builtins import str

from .base import ConfigObject, ConfigOption
from .command import Command


IPTABLES_WAIT = "5"


def start_iptables_command(cmd, *args):
    return [cmd, "--wait", IPTABLES_WAIT] + list(args)


class ConfigDefaults(ConfigObject):
    typename = "defaults"

    options = [
        ConfigOption(name="input", default="ACCEPT"),
        ConfigOption(name="output", default="ACCEPT"),
        ConfigOption(name="forward", default="ACCEPT"),
        ConfigOption(name="disable_ipv6", type=bool)
    ]

    def getName(self):
        # There should only be one defaults section.  If we return a constant
        # string for all instances, we can match them across file versions.
        return "SINGLETON"

    def get_iptables(self):
        """
        Get the list of iptables commands to use (iptables / ip6tables).
        """
        if self.disable_ipv6:
            return ["iptables"]
        else:
            return ["iptables", "ip6tables"]

    def apply(self, allConfigs):
        commands = list()

        for iptables in self.get_iptables():
            for path in ["input", "output", "forward"]:
                # Create the delegate_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--new", "delegate_"+path]
                commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Jump to delegate_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--append", path.upper(), "--jump",
                        "delegate_"+path]
                commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Create the X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--new", path+"_rule"]
                commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Jump to X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--append", path.upper(), "--jump",
                        path+"_rule"]
                commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Add a rule at the end with the default policy.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--append", path.upper(), "--jump",
                        getattr(self, path)]
                commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            for path in ["prerouting", "postrouting"]:
                # Create the delegate_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--new", "delegate_"+path]
                commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Jump to delegate_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--append", path.upper(), "--jump",
                        "delegate_"+path]
                commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Create the X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--new", path+"_rule"]
                commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Jump to X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--append", path.upper(), "--jump",
                        path+"_rule"]
                commands.append((self.PRIO_IPTABLES_TOP, Command(cmd, self)))

        return commands

    def revert(self, allConfigs):
        commands = list()

        for iptables in self.get_iptables():
            for path in ["prerouting", "postrouting"]:
                # Jump to X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--delete", path.upper(), "--jump",
                        path+"_rule"]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Flush the X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--flush", path+"_rule"]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Delete the X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--delete-chain", path+"_rule"]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Jump to delegate_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--delete", path.upper(), "--jump",
                        "delegate_"+path]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Flush the delegate_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--flush", "delegate_"+path]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Delete the delegate_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "nat", "--delete-chain", "delegate_"+path]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

            for path in ["input", "output", "forward"]:
                # Jump to X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--delete", path.upper(), "--jump",
                        path+"_rule"]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Flush the X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--flush", path+"_rule"]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Delete the X_rule chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--delete-chain", path+"_rule"]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Jump to paradrop_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--delete", path.upper(), "--jump",
                        "delegate_"+path]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Flush the paradrop_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--flush", "delegate_"+path]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Delete the paradrop_X chain.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--delete-chain", "delegate_"+path]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

                # Delete the default rule.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--delete", path.upper(), "--jump",
                        getattr(self, path)]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

        return commands

    def updateApply(self, new, allConfigs):
        commands = list()

        for iptables in new.get_iptables():
            for path in ["input", "output", "forward"]:
                if getattr(self, path) == getattr(new, path):
                    # Skip if no change.
                    continue

                # Add the new default rule.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--append", path.upper(), "--jump",
                        getattr(new, path)]
                commands.append((new.PRIO_IPTABLES_TOP, Command(cmd, new)))

        return commands

    def updateRevert(self, new, allConfigs):
        commands = list()

        for iptables in self.get_iptables():
            for path in ["input", "output", "forward"]:
                if getattr(self, path) == getattr(new, path):
                    # Skip if no change.
                    continue

                # Delete the old default rule.
                cmd = start_iptables_command(iptables) + ["--table",
                        "filter", "--delete", path.upper(), "--jump",
                        getattr(self, path)]
                commands.append((-self.PRIO_IPTABLES_TOP, Command(cmd, self)))

        return commands


class ConfigZone(ConfigObject):
    typename = "zone"

    options = [
        ConfigOption(name="name", required=True),
        ConfigOption(name="network", type=list),
        ConfigOption(name="masq", type=bool, default=False),
        ConfigOption(name="masq_src", type=list, default=["0.0.0.0/0"]),
        ConfigOption(name="masq_dest", type=list, default=["0.0.0.0/0"]),
        ConfigOption(name="conntrack", type=bool, default=False),
        ConfigOption(name="input", default="RETURN"),
        ConfigOption(name="forward", default="RETURN"),
        ConfigOption(name="output", default="RETURN"),
        ConfigOption(name="family", default="any")
    ]

    def get_iptables(self):
        """
        Get the list of iptables commands to use (iptables / ip6tables).
        """
        if self.family == "ipv4":
            return ["iptables"]
        elif self.family == "ipv6":
            return ["ip6tables"]
        else:
            return ["iptables", "ip6tables"]

    def setup(self):
        self._interfaces = list()

    def __commands_iptables(self, allConfigs, action, prio):
        commands = list()

        for interface in self._interfaces:
            for iptables in self.get_iptables():
                # Jump to zone input chain.
                chain = "zone_{}_input".format(self.name)
                cmd = start_iptables_command(iptables) + [
                        "--table", "filter",
                        action, "delegate_input",
                        "--in-interface", interface.config_ifname,
                        "--jump", chain]
                commands.append((prio, Command(cmd, self)))

                # If conntrack is enabled, allow incoming traffic that is
                # associated with allowed outgoing traffic.
                if self.conntrack:
                    comment = "zone {} conntrack".format(self.name)
                    cmd = start_iptables_command(iptables) + [
                            "--table", "filter",
                            action, "input_rule",
                            "--in-interface", interface.config_ifname,
                            "--match", "state", "--state", "ESTABLISHED,RELATED",
                            "--match", "comment", "--comment", comment,
                            "--jump", "ACCEPT"]
                    commands.append((prio, Command(cmd, self)))

                # Implement default policy for zone.
                comment = "zone {} default".format(self.name)
                cmd = start_iptables_command(iptables) + [
                        "--table", "filter",
                        action, "input_rule",
                        "--in-interface", interface.config_ifname,
                        "--match", "comment", "--comment", comment,
                        "--jump", self.input]
                commands.append((prio, Command(cmd, self)))

                # Jump to zone output chain.
                chain = "zone_{}_output".format(self.name)
                cmd = start_iptables_command(iptables) + [
                        "--table", "filter",
                        action, "delegate_output",
                        "--out-interface", interface.config_ifname,
                        "--jump", chain]
                commands.append((prio, Command(cmd, self)))

                # Implement default policy for zone.
                cmd = start_iptables_command(iptables) + [
                        "--table", "filter",
                        action, "output_rule",
                        "--out-interface", interface.config_ifname,
                        "--match", "comment", "--comment", comment,
                        "--jump", self.output]
                commands.append((prio, Command(cmd, self)))

                # Jump to zone forward chain.
                chain = "zone_{}_forward".format(self.name)
                cmd = start_iptables_command(iptables) + [
                        "--table", "filter",
                        action, "delegate_forward",
                        "--in-interface", interface.config_ifname,
                        "--jump", chain]
                commands.append((prio, Command(cmd, self)))

                # Implement default policy for zone.
                cmd = start_iptables_command(iptables) + [
                        "--table", "filter",
                        action, "forward_rule",
                        "--in-interface", interface.config_ifname,
                        "--match", "comment", "--comment", comment,
                        "--jump", self.forward]
                commands.append((prio, Command(cmd, self)))

                # Jump to zone prerouting chain.
                chain = "zone_{}_prerouting".format(self.name)
                cmd = start_iptables_command(iptables) + [
                        "--table", "nat",
                        action, "delegate_prerouting",
                        "--in-interface", interface.config_ifname,
                        "--jump", chain]
                commands.append((prio, Command(cmd, self)))

                # Jump to zone postrouting chain.
                chain = "zone_{}_postrouting".format(self.name)
                cmd = start_iptables_command(iptables) + [
                        "--table", "nat",
                        action, "delegate_postrouting",
                        "--out-interface", interface.config_ifname,
                        "--jump", chain]
                commands.append((prio, Command(cmd, self)))

            # Masquerade rules are for IPv4 only, so add them outside the
            # iptables loop above.
            if self.masq:
                for src in self.masq_src:
                    for dest in self.masq_dest:
                        comment = "zone {} masq".format(self.name)
                        cmd = start_iptables_command("iptables") + [
                                "--table", "nat",
                               action, "POSTROUTING",
                               "--out-interface", interface.config_ifname,
                               "--source", src,
                               "--destination", dest,
                               "--match", "comment", "--comment", comment,
                               "--jump", "MASQUERADE"]
                        commands.append((prio, Command(cmd, self)))

        return commands

    def apply(self, allConfigs):
        # Initialize the list of network:interface sections.
        self._interfaces = list()
        if self.network is not None:
            for networkName in self.network:
                # Look up the interface - may fail.
                interface = self.lookup(allConfigs, "network", "interface", networkName)
                self._interfaces.append(interface)

        commands = list()

        for iptables in self.get_iptables():
            for path in ["input", "output", "forward"]:
                # Create the zone_NAME_X chain.
                chain = "zone_{}_{}".format(self.name, path)
                cmd = start_iptables_command(iptables) + [
                        "--table", "filter",
                        "--new", chain]
                commands.append((self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

            for path in ["prerouting", "postrouting"]:
                # Create the zone_NAME_X chain.
                chain = "zone_{}_{}".format(self.name, path)
                cmd = start_iptables_command(iptables) + [
                        "--table", "nat",
                        "--new", chain]
                commands.append((self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        commands.extend(self.__commands_iptables(allConfigs, "--append",
                self.PRIO_IPTABLES_ZONE))

        if self.masq:
            self.manager.forwardingCount += 1
            if self.manager.forwardingCount == 1:
                cmd = ["sysctl", "-w", "net.ipv4.conf.all.forwarding=1"]
                commands.append((self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

                cmd = ["sysctl", "-w", "net.ipv6.conf.all.forwarding=1"]
                commands.append((self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        return commands

    def revert(self, allConfigs):
        commands = self.__commands_iptables(allConfigs, "--delete",
                -self.PRIO_IPTABLES_ZONE)

        if self.masq:
            self.manager.forwardingCount -= 1
            if self.manager.forwardingCount == 0:
                cmd = ["sysctl", "-w", "net.ipv4.conf.all.forwarding=0"]
                commands.append((-self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

                cmd = ["sysctl", "-w", "net.ipv6.conf.all.forwarding=0"]
                commands.append((-self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        for iptables in self.get_iptables():
            pairs = [
                ("filter", "input"),
                ("filter", "output"),
                ("filter", "forward"),
                ("nat", "prerouting"),
                ("nat", "postrouting")
            ]

            for table, path in pairs:
                chain = "zone_{}_{}".format(self.name, path)

                # Flush the zone_NAME_X chain, so that we do not get an error
                # with the delete command.
                cmd = start_iptables_command(iptables) + [
                        "--table", table,
                        "--flush", chain]
                commands.append((-self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

                # Delete the zone_NAME_X chain.
                cmd = start_iptables_command(iptables) + [
                        "--table", table,
                        "--delete-chain", chain]
                commands.append((-self.PRIO_IPTABLES_ZONE, Command(cmd, self)))

        # Reset the list of network:interface sections.
        self._interfaces = list()

        return commands


class ConfigForwarding(ConfigObject):
    typename = "forwarding"

    options = [
        ConfigOption(name="src", required=True),
        ConfigOption(name="dest", required=True)
    ]

    def __commands(self, allConfigs, action, prio):
        commands = list()

        chain = "zone_{}_forward".format(self.src)
        for dest_iface in self.dest_interfaces:
            comment = "forwarding {} -> {}".format(self.src, self.dest)
            cmd = start_iptables_command("iptables") + [
                    "--table", "filter",
                    action, chain,
                    "--out-interface", dest_iface.config_ifname,
                    "--match", "comment", "--comment", comment,
                    "--jump", "ACCEPT"]
            commands.append((prio, Command(cmd, self)))

        return commands

    def apply(self, allConfigs):
        # Look up src_zone in order to indicate dependency.  If the source zone
        # changes, we need to reapply this forwarding section as well.
        self.src_zone = self.lookup(allConfigs, "firewall", "zone", self.src)

        self.dest_zone = self.lookup(allConfigs, "firewall", "zone", self.dest)

        # Initialize the list of network:interface sections.
        self.dest_interfaces = list()
        if self.dest_zone.network is not None:
            for networkName in self.dest_zone.network:
                # Look up the interface - may fail.
                interface = self.lookup(allConfigs, "network", "interface", networkName)
                self.dest_interfaces.append(interface)

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
            cmd = start_iptables_command("iptables") + ["--table", "nat",
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
            cmd = ["sysctl", "-w", "net.ipv4.conf.all.forwarding=1"]
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
            cmd = ["sysctl", "-w", "net.ipv4.conf.all.forwarding=0"]
            commands.append((-self.PRIO_CONFIG_IFACE, Command(cmd, self)))

        return commands


class ConfigRule(ConfigObject):
    typename = "rule"

    options = [
        ConfigOption(name="name", required=False),
        ConfigOption(name="src"),
        ConfigOption(name="src_ip"),
        ConfigOption(name="src_port"),
        ConfigOption(name="src_mac"),
        ConfigOption(name="proto"),
        ConfigOption(name="dest"),
        ConfigOption(name="dest_ip"),
        ConfigOption(name="dest_port"),
        ConfigOption(name="target", required=True),
        ConfigOption(name="family", default="any"),
        ConfigOption(name="extra")
    ]

    def get_iptables(self):
        """
        Get the list of iptables commands to use (iptables / ip6tables).
        """
        # Check if the rule explicitly specifies the family.
        if self.family == "ipv4":
            return ["iptables"]
        elif self.family == "ipv6":
            return ["ip6tables"]

        # If the rule specifies the source address, use that as a hint.
        if self.src_ip is not None:
            addr = ipaddress.ip_network(str(self.src_ip), strict=False)
            if addr.version == 4:
                return ["iptables"]
            elif addr.version == 6:
                return ["ip6tables"]

        # If the rule specifies the destination address, use that as a hint.
        if self.dest_ip is not None:
            addr = ipaddress.ip_network(str(self.dest_ip), strict=False)
            if addr.version == 4:
                return ["iptables"]
            elif addr.version == 6:
                return ["ip6tables"]

        # Default is to generate rules for both IPv4 and IPv6.
        return ["iptables", "ip6tables"]

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

        for iptables in self.get_iptables():
            # Put together the common options for rules.
            cmd = start_iptables_command(iptables) + [
                    "--wait", IPTABLES_WAIT,
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

            if self.name:
                cmd.extend(["--match", "comment", "--comment", self.name])

            commands.append((prio, Command(cmd, self)))

        return commands

    def apply(self, allConfigs):
        return self.__commands(allConfigs, "--append", self.PRIO_IPTABLES_RULE)

    def revert(self, allConfigs):
        return self.__commands(allConfigs, "--delete", -self.PRIO_IPTABLES_RULE)
