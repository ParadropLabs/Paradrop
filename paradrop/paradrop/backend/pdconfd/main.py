"""
This module listens for D-Bus messages and triggers reloading of configuration
files.  This module is the service side of the implementation.  If you want to
issue reload commands to the service, see the client.py file instead.

Operation:
    - When triggered, read in UCI configuration files.
    - Pass sections off to appropriate handlers (interface, etc.).
    - Perform some validation (check for required options).
    - Emit commands (start/stop daemon, ip, iw, etc.) into a queue.
    - Issue commands, maybe rollback on failure.
    - Update known state of the system.

Reference:
http://excid3.com/blog/an-actually-decent-python-dbus-tutorial/
"""
import atexit
import sys

from twisted.internet import reactor, defer
from txdbus import client, objects, error
from txdbus.interface import DBusInterface, Method

from .config.manager import ConfigManager

service_name = "com.paradrop.config"
service_path = "/"

# Do not try to use this from outside the pdconfd code.
# Use the functions in backend.pdconfd.client instead.
config_manager = None


class ConfigService(objects.DBusObject):
    dbusInterfaces = [
        DBusInterface(service_name,
                      Method("Reload", arguments="s", returns="s"),
                      Method("ReloadAll", returns="s"),
                      Method("Test", returns="b"),
                      Method("UnloadAll", returns="b"),
                      Method("WaitSystemUp", returns="s"))
    ]

    def dbus_Reload(self, name):
        return config_manager.loadConfig(name)

    def dbus_ReloadAll(self):
        return config_manager.loadConfig()

    def dbus_Test(self):
        return True

    def dbus_UnloadAll(self):
        return config_manager.unload()

    def dbus_WaitSystemUp(self):
        return config_manager.waitSystemUp()


@defer.inlineCallbacks
def listen():
    service = ConfigService()

    # Things get messy if pdconfd is restarted with running chutes.  Then it
    # will try to reconfigure the system.  One easy solution is to unload the
    # configuration before exiting.
    reactor.addSystemEventTrigger('before', 'shutdown',
                                  config_manager.unload)

    # Now load all of the configuration for the first time.
    config_manager.loadConfig()

    try:
        conn = yield client.connect(reactor, busAddress="system")
        conn.exportObject(service)
        yield conn.requestBusName(service_name)
    except error.DBusException as e:
        print("Failed to export DBus object: {}".format(e))
        reactor.stop()


def run_thread():
    """
    Start pdconfd service as a thread.

    This function schedules pdconfd to run as a thread and returns immediately.
    """
    config_manager = ConfigManager()
    reactor.callFromThread(listen)


def run_pdconfd():
    """
    Start pdconfd daemon.

    This enters the pdconfd main loop.
    """
    config_manager = ConfigManager()
    reactor.callWhenRunning(listen)
    reactor.run()

if __name__ == "__main__":
    run_pdconfd()
