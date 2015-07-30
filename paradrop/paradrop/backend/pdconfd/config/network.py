from .base import ConfigObject
from .command import Command


class ConfigInterface(ConfigObject):
    typename = "interface"

    options = [
        {"name": "proto", "type": str, "required": True, "default": None},
        {"name": "ifname", "type": str, "required": True, "default": None},
        {"name": "enabled", "type": bool, "required": False, "default": True},
        {"name": "ipaddr", "type": str, "required": False, "default": None},
        {"name": "netmask", "type": str, "required": False, "default": None}
    ]

    def commands(self, allConfigs):
        commands = list()
        if self.proto == "static":
            cmd = ["ip", "addr", "flush", "dev", self.ifname]
            commands.append((Command.PRIO_CONFIG_IFACE, cmd))

            cmd = ["ip", "addr", "add",
                   "{}/{}".format(self.ipaddr, self.netmask),
                   "dev", self.ifname]
            commands.append((Command.PRIO_CONFIG_IFACE, cmd))

            updown = "up" if self.enabled else "down"
            cmd = ["ip", "link", "set", "dev", self.ifname, updown]
            commands.append((Command.PRIO_CONFIG_IFACE, cmd))

        return commands

    def undoCommands(self, allConfigs):
        commands = list()
        if self.proto == "static":
            # Remove the IP address that we added.
            cmd = ["ip", "addr", "del",
                   "{}/{}".format(self.ipaddr, self.netmask),
                   "dev", self.ifname]
            commands.append((Command.PRIO_CONFIG_IFACE, cmd))

        return commands
