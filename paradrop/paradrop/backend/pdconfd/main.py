"""
This module listens for D-Bus messages and triggers reloading of
configuration files.

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

from twisted.internet import reactor, defer
from txdbus import client, objects, error
from txdbus.interface import DBusInterface, Method

import sys

from .config.manager import ConfigManager

service_name="com.paradrop.config"
service_path="/"

class ConfigService(objects.DBusObject):
    dbusInterfaces = [
        DBusInterface(service_name, 
            Method("Reload", arguments="s", returns="s"),
            Method("ReloadAll", returns="s"),
            Method("Test", returns="s"),
            Method("UnloadAll", returns="b"),
            Method("WaitSystemUp", returns="s"))
    ]

    def __init__(self):
        super(ConfigService, self).__init__(service_path)
        self.configManager = ConfigManager()

    def dbus_Reload(self, name):
        print("Asked to reload {}.".format(name))
        return self.configManager.loadConfig(name)

    def dbus_ReloadAll(self):
        print("Asked to reload configuration files.")
        return self.configManager.loadConfig()

    def dbus_Test(self):
        return "D-Bus is working!"

    def dbus_UnloadAll(self):
        print("Asked to unload configuration.")
        return self.configManager.unload()

    def dbus_WaitSystemUp(self):
        print("Waiting for system to be up.")
        return self.configManager.waitSystemUp()

@defer.inlineCallbacks
def listen():
    service = ConfigService()
    service.configManager.loadConfig()

    try:
        conn = yield client.connect(reactor, busAddress="system")
        conn.exportObject(service)
        yield conn.requestBusName(service_name)
    except error.DBusException as e:
        print("Failed to export DBus object: {}".format(e))
        reactor.stop()

def run_pdconfd():
    reactor.callWhenRunning(listen)
    reactor.run()

if __name__=="__main__":
    run_pdconfd()

