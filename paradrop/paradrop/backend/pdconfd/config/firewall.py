from .base import ConfigObject
from .command import Command


class ConfigRedirect(ConfigObject):
    typename = "redirect"

    options = [
        {"name": "src", "type": str, "required": False, "default": None},
        {"name": "src_ip", "type": str, "required": False, "default": None},
        {"name": "src_dip", "type": str, "required": False, "default": None},
        {"name": "src_port", "type": str, "required": False, "default": None},
        {"name": "src_dport", "type": str, "required": False, "default": None},
        {"name": "proto", "type": str, "required": True, "default": "tcpudp"},
        {"name": "dest", "type": str, "required": False, "default": None},
        {"name": "dest_ip", "type": str, "required": False, "default": None},
        {"name": "dest_port", "type": str, "required": False, "default": None},
        {"name": "target", "type": str, "required": False, "default": "DNAT"}
    ]

    # Any of these values will be interpreted to mean that --proto and ports
    # should not be specified in the iptables rule.
    ANY_PROTO = set([None, "any", "none"])

    def __commands_dnat(self, allConfigs, action, prio):
        """
        Generate DNAT iptables rules.
        """
        commands = list()

        src_zone = self.lookup(allConfigs, "zone", self.src)

        # Special cases:
        # None->skip protocol and port arguments,
        # tcpudp->[tcp, udp]
        if self.proto in self.ANY_PROTO:
            protocols = [None]
        elif self.proto == "tcpudp":
            protocols = ["tcp", "udp"]
        else:
            protocols = [self.proto]

        for interface in src_zone.interfaces(allConfigs):
            for proto in protocols:
                cmd = ["iptables", "--table", "nat",
                       action, "PREROUTING",
                       "--in-interface",
                       interface.config_ifname]

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

                cmd.extend(["--match", "comment", "--comment",
                            "pdconfd {} {}".format(self.typename, self.name)])

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


class ConfigZone(ConfigObject):
    typename = "zone"

    options = [
        {"name": "name", "type": str, "required": True, "default": None},
        {"name": "network", "type": list, "required": False, "default": None},
        {"name": "masq", "type": bool, "required": False, "default": False},
        {"name": "input", "type": str, "required": False, "default": "DROP"},
        {"name": "forward", "type": str, "required": False, "default": "DROP"},
        {"name": "output", "type": str, "required": False, "default": "DROP"}
    ]

    def interfaces(self, allConfigs):
        """
        List of interfaces in this zone (generator).
        """
        if self.network is not None:
            for networkName in self.network:
                # Look up the interface - may fail.
                interface = self.lookup(allConfigs, "interface", networkName)
                yield interface

    def __commands_iptables(self, allConfigs, action, prio):
        commands = list()

        if self.masq:
            for interface in self.interfaces(allConfigs):
                cmd = ["iptables", "--table", "nat",
                       action, "POSTROUTING",
                       "--out-interface", interface.config_ifname,
                       "--jump", "MASQUERADE",
                       "--match", "comment", "--comment",
                       "pdconfd {} {}".format(self.typename, self.name)]
                commands.append((prio, Command(cmd, self)))

        return commands

    def apply(self, allConfigs):
        commands = self.__commands_iptables(allConfigs, "--insert",
                self.PRIO_CONFIG_IFACE)

        if self.masq:
            self.manager.forwardingCount += 1
            if self.manager.forwardingCount == 1:
                cmd = ["sysctl", "--write",
                       "net.ipv4.conf.all.forwarding=1"]
                commands.append((self.PRIO_CONFIG_IFACE, Command(cmd, self)))

        return commands

    def revert(self, allConfigs):
        commands = self.__commands_iptables(allConfigs, "--delete",
                -self.PRIO_CONFIG_IFACE)

        if self.masq:
            self.manager.forwardingCount -= 1
            if self.manager.forwardingCount == 0:
                cmd = ["sysctl", "--write",
                       "net.ipv4.conf.all.forwarding=0"]
                commands.append((-self.PRIO_CONFIG_IFACE, Command(cmd, self)))
        return commands
