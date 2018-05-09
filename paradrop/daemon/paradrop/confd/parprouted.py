from .base import ConfigObject, ConfigOption
from .command import Command, KillCommand


class ConfigBridge(ConfigObject):
    typename = "bridge"

    options = [
        ConfigOption(name="interfaces", type=list, required=True)
    ]

    def apply(self, allConfigs):
        commands = list()

        cmd = ["parprouted"]
        for section_name in self.interfaces:
            interface = self.lookup(allConfigs, "network", "interface", section_name)
            cmd.append(interface.config_ifname)

        self.daemon_command = Command(cmd, self)
        commands.append((self.PRIO_START_DAEMON, self.daemon_command))

        return commands

    def revert(self, allConfigs):
        commands = list()

        commands.append((-self.PRIO_START_DAEMON,
            KillCommand(self.daemon_command.pid, self)))

        return commands
