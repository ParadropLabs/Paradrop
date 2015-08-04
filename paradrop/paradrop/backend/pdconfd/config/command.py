import subprocess

from pdtools.lib.output import out

class Command(object):
    # Command priorities, lower numbers executed first.
    PRIO_CREATE_IFACE = 10
    PRIO_CONFIG_IFACE = 20
    PRIO_START_DAEMON = 30
    PRIO_ADD_IPTABLES = 40
    PRIO_DELETE_IFACE = 50

    def __init__(self, priority, command, parent=None):
        """
        Construct command object.

        priority: integer value, should be one of the PRIO_* constants
        command: array of strings specifying command and arguments
        parent: parent object (should be ConfigObject subclass)
        """
        self.priority = priority
        self.command = command
        self.parent = parent

        # These are set after execute completes.
        self.pid = None
        self.result = None

    def __str__(self):
        return " ".join(self.command)

    def execute(self):
        try:
            proc = subprocess.Popen(self.command)
            self.pid = proc.pid
            self.result = proc.wait()
            out.info('Command "{}" returned {}\n'.format(
                     " ".join(self.command), self.result))
        except OSError as e:
            out.info('Command "{}" raised exception {}\n'.format(
                     " ".join(self.command), e))
            self.result = e

        if self.parent is not None:
            self.parent.executed.append(self)

        return (self.result == 0)

    def success(self):
        """
        Returns True if the command was successfully executed.
        """
        return (self.result == 0)
