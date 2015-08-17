from .base import ConfigObject
from .command import Command


class ConfigInterface(ConfigObject):
    typename = "interface"

    options = [
        {"name": "proto", "type": str, "required": True, "default": None},
        {"name": "ifname", "type": list, "required": True, "default": None},
        {"name": "type", "type": str, "required": False, "default": None},
        {"name": "enabled", "type": bool, "required": False, "default": True},
        {"name": "ipaddr", "type": str, "required": False, "default": None},
        {"name": "netmask", "type": str, "required": False, "default": None}
    ]

    def setup(self):
        # For which interface are we setting the IP address?  If it's a bridge,
        # we create a bridge interface and set its address; otherwise, we take
        # the "ifname" option.
        if self.type == "bridge":
            self.config_ifname = "br-{}".format(self.name)
        else:
            self.config_ifname = self.ifname[0]

    def addToBridge(self, ifname, bridge):
        """ Generate commands to add ifname to bridge. """
        commands = list()

        cmd = ["ip", "link", "set", "dev", ifname, "promisc", "on"]
        commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        cmd = ["ip", "link", "set", "dev", ifname, "up"]
        commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        cmd = ["ip", "link", "set", "dev", ifname, "master", bridge]
        commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        return commands

    def removeFromBridge(self, ifname):
        """ Generate commands to add ifname to bridge. """
        commands = list()

        cmd = ["ip", "link", "set", "dev", ifname, "promisc", "off"]
        commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        cmd = ["ip", "link", "set", "dev", ifname, "down"]
        commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        cmd = ["ip", "link", "set", "dev", ifname, "nomaster"]
        commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        return commands

    def commands(self, allConfigs):
        commands = list()

        if self.type == "bridge":
            cmd = ["ip", "link", "add", "name", self.config_ifname, "type",
                   "bridge"]
            commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

            # Add all of the interfaces to the bridge.
            for ifname in self.ifname:
                commands.extend(self.addToBridge(ifname, self.config_ifname))

        if self.proto == "static":
            cmd = ["ip", "addr", "flush", "dev", self.config_ifname]
            commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

            cmd = ["ip", "addr", "add",
                   "{}/{}".format(self.ipaddr, self.netmask),
                   "dev", self.config_ifname]
            commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

            updown = "up" if self.enabled else "down"
            cmd = ["ip", "link", "set", "dev", self.config_ifname, updown]
            commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        return commands

    def undoCommands(self, allConfigs):
        commands = list()

        if self.proto == "static":
            # Remove the IP address that we added.
            cmd = ["ip", "addr", "del",
                   "{}/{}".format(self.ipaddr, self.netmask),
                   "dev", self.config_ifname]
            commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        if self.type == "bridge":
            # Remove all of the interfaces from the bridge.
            for ifname in self.ifname:
                commands.extend(self.removeFromBridge(ifname))

            cmd = ["ip", "link", "delete", self.config_ifname]
            commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        return commands

    def update(self, new, allConfigs):
        # Major changes require reverting the current config and loading the
        # new one.
        if self.proto != new.proto or self.type != new.type:
            return None

        commands = list()

        # May have changed the IP address.
        if self.proto == "static":
            cmd = ["ip", "addr", "change",
                   "{}/{}".format(self.ipaddr, self.netmask),
                   "dev", self.config_ifname]
            commands.append(Command(Command.PRIO_CONFIG_IFACE, cmd, self))

        if self.type == "bridge":
            old_ifnames = set(self.ifname)
            new_ifnames = set(new.ifname)

            # Remove interfaces that are not in the new bridge.
            for ifname in (old_ifnames - new_ifnames):
                commands.extend(self.removeFromBridge(ifname))

            # Add interfaces that were not in the old bridge.
            for ifname in (new_ifnames - old_ifnames):
                commands.extend(self.addToBridge(ifname, self.config_ifname))
