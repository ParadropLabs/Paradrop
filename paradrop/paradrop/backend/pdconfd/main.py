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
from paradrop.lib import settings

from .config.manager import ConfigManager

service_name = "com.paradrop.config"
service_path = "/"


class ConfigService(objects.DBusObject):
    dbusInterfaces = [
        DBusInterface(service_name,
                      Method("Reload", arguments="s", returns="s"),
                      Method("ReloadAll", returns="s"),
                      Method("Test", returns="b"),
                      Method("UnloadAll", returns="b"),
                      Method("WaitSystemUp", returns="s"))
    ]

    configManager = None

    def __init__(self):
        super(ConfigService, self).__init__(service_path)

    def dbus_Reload(self, name):
        return ConfigService.configManager.loadConfig(name)

    def dbus_ReloadAll(self):
        return ConfigService.configManager.loadConfig()

    def dbus_Test(self):
        return True

    def dbus_UnloadAll(self):
        return ConfigService.configManager.unload()

    def dbus_WaitSystemUp(self):
        return ConfigService.configManager.waitSystemUp()


@defer.inlineCallbacks
def listen():
    service = ConfigService()

    # Things get messy if pdconfd is restarted with running chutes.  Then it
    # will try to reconfigure the system.  One easy solution is to unload the
    # configuration before exiting.
    reactor.addSystemEventTrigger('before', 'shutdown',
                                  ConfigService.configManager.unload)

    # Now load all of the configuration for the first time.
    ConfigService.configManager.loadConfig()

    try:
        conn = yield client.connect(reactor, busAddress="system")
        conn.exportObject(service)
        yield conn.requestBusName(service_name)
    except error.DBusException as e:
        print("Failed to export DBus object: {}".format(e))


def run_thread():
    """
    Start pdconfd service as a thread.

    This function schedules pdconfd to run as a thread and returns immediately.
    """
    ConfigService.configManager = ConfigManager(settings.PDCONFD_WRITE_DIR)
    reactor.callFromThread(listen)


def run_pdconfd():
    """
    Start pdconfd daemon.

    This enters the pdconfd main loop.
    """
    ConfigService.configManager = ConfigManager(settings.PDCONFD_WRITE_DIR)
    reactor.callWhenRunning(listen)
    reactor.run()
