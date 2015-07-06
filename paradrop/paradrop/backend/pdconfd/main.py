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

from config import ConfigManager

service_name="com.paradrop.config"
service_path="/"

class ConfigService(objects.DBusObject):
    dbusInterfaces = [
        DBusInterface(service_name, 
            Method("Reload", arguments="s", returns="b"),
            Method("ReloadAll", returns="b"),
            Method("Test", returns="s"))
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

@defer.inlineCallbacks
def listen():
    try:
        conn = yield client.connect(reactor, busAddress="system")
        conn.exportObject(ConfigService())
        yield conn.requestBusName(service_name)
    except error.DBusException as e:
        print("Failed to export DBus object: {}".format(e))
        reactor.stop()

