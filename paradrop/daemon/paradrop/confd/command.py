import errno
import os
import signal
import six
import subprocess
import time

from paradrop.base.output import out


def kill(pid, kill_signal=4, timeout=8):
    """
    Kill a child process and wait with timeout.

    1. Send a SIGTERM signal to the process.
    2. Wait up to `kill_signal` seconds for the process to exit.
    3. If process is still running, send a SIGKILL signal.
    4. Wait up to `timeout` seconds (cumulative with `kill_signal`) for the
    process to exit.

    Returns True if the process exited before `timeout` seconds elapsed.
    """
    os.kill(pid, signal.SIGTERM)

    start = time.time()
    while (time.time() - start) < kill_signal:
        time.sleep(0.1)

        try:
            # waitpid returns (0, 0) if the process is still running.
            # Otherwise, it returns (pid, status).
            opid, status = os.waitpid(pid, os.WNOHANG)
            if opid == pid:
                return True
        except OSError as error:
            # I think ECHILD means there is no process with the given pid.
            if error.errno == errno.ECHILD:
                return True
            else:
                raise error

    try:
        os.kill(pid, signal.SIGKILL)
    except OSError as error:
        if error.errno == errno.ESRCH:
            # The process exited between the time that we checked it and when
            # we tried to send a SIGKILL.  This is not an error.
            return True
        else:
            raise error

    while (time.time() - start) < timeout:
        time.sleep(0.1)

        try:
            # waitpid returns (0, 0) if the process is still running.
            # Otherwise, it returns (pid, status).
            opid, status = os.waitpid(pid, os.WNOHANG)
            if opid == pid:
                return True
        except OSError as error:
            # I think ECHILD means there is no process with the given pid.
            if error.errno == errno.ECHILD:
                return True
            else:
                raise error

    return False


class CommandList(list):
    def __contains__(self, s):
        """
        Test if the list contains a given string.
        """
        return any(s in cmd for prio, cmd in self)

    def append(self, priority, command):
        super(CommandList, self).append((priority, command))

    def commands(self):
        """
        Iterate over commands in order by priority.

        Commands are first sorted by assigned priority.  Within each priority
        level, the order in which they were added is maintained.
        """
        result = list()
        for i in range(len(self)):
            prio, cmd = self[i]
            result.append((prio, i, cmd))

        result.sort()

        for prio, i, cmd in result:
            yield cmd


class Command(object):
    def __init__(self, command, parent=None, ignoreFailure=False):
        """
        Construct command object.

        command: array of strings specifying command and arguments
                 Passing a single string is also supported if there are
                 no spaces within arguments (only between them).
        parent: parent object (should be ConfigObject subclass)
        """
        self.parent = parent
        self.ignoreFailure = ignoreFailure

        if type(command) == list:
            self.command = [str(v) for v in command]
        elif isinstance(command, six.string_types):
            self.command = command.split()

        # These are set after execute completes.
        self.pid = None
        self.result = None

    def __contains__(self, s):
        """
        Test if command contains given string.

        Example:
        If the cmd.command = ['kill', '1'], then ("kill" in cmd) will return True.
        """
        return (s in str(self))

    def __str__(self):
        return " ".join(self.command)

    def execute(self):
        try:
            proc = subprocess.Popen(self.command, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
            self.pid = proc.pid
            for line in proc.stdout:
                out.verbose("{} {}: {}".format(self.command[0], self.pid, line))
            for line in proc.stderr:
                out.verbose("{} {}: {}".format(self.command[0], self.pid, line))
            self.result = proc.wait()
            if self.result == 0:
                out.verbose('Command "{}" returned {}\n'.format(
                         " ".join(self.command), self.result))
            else:
                out.info('Command "{}" returned {}\n'.format(
                         " ".join(self.command), self.result))
        except Exception as e:
            out.info('Command "{}" raised exception {}\n'.format(
                     " ".join(self.command), e))
            self.result = e

        if self.parent is not None:
            self.parent.executed.append(self)

        return (self.ignoreFailure or self.result == 0)

    def success(self):
        """
        Returns True if the command was successfully executed.
        """
        return (self.ignoreFailure or self.result == 0)


class ErrorCommand(Command):
    """
    Special command object that indicates an error occurred.
    """
    def __init__(self, error, parent=None):
        super(ErrorCommand, self).__init__([], parent)
        self.error = error

    def execute(self):
        out.info("An error occurred: {}".format(self.error))

    def success(self):
        return False


class FunctionCommand(Command):
    """
    Command that runs a Python function.
    """
    def __init__(self, parent, function, *args, **kwargs):
        command = [function.__name__]
        command.extend(args)
        for key, value in six.iteritems(kwargs):
            command.append("{}={}".format(key, value))

        super(FunctionCommand, self).__init__(command, parent)

        self.function = function
        self.args = args
        self.kwargs = kwargs

        self.result = None

    def execute(self):
        self.result = self.function(*self.args, **self.kwargs)


class KillCommand(Command):
    """
    Special command object for killing a process
    """
    def __init__(self, pid, parent=None):
        """
        Create a kill command

        The pid argument can either be a real pid (e.g. kill 12345) or a path
        to a file containing the pid.

        If the pid is coming from a file, it will be resolved at the time that
        execute is called.  Before that time, the command will be stored
        internally as ["kill", "/path/to/file"].  This is not a real command,
        but it is meaningful if you print the command object.
        """
        # This will not be a valid command if pid is a file path.
        command = ["kill", pid]

        super(KillCommand, self).__init__(command, parent)

        # Is it a numeric pid or a path to a pid file?
        try:
            self.pid = int(pid)
            self.fromFile = False
        except ValueError:
            self.pid = pid
            self.fromFile = True

    def getPid(self):
        if self.fromFile:
            try:
                with open(self.pid, "r") as inputFile:
                    return int(inputFile.read().strip())
            except:
                # No pid file --- maybe it was not running?
                out.warn("File not found: {}\n".format(self.pid))
                return None
        else:
            return self.pid

    def execute(self):
        pid = self.getPid()

        if pid is None:
            self.result = 0
            return True

        try:
            retval = kill(pid)
            self.result = 0
            out.info('Command "kill {}" returned {}\n'.format(pid, retval))
        except Exception as e:
            out.info('Command "kill {}" raised exception {}\n'.format(pid, e))
            self.result = e

        return (self.result == 0)
