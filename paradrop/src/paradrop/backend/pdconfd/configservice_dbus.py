"""
This module listens for D-Bus messages and triggers reloading of configuration files.
This module is the service side of the implementation.
If you want to issue reload commands to the service, see the client-dbus.py file instead.

Operation:
    - When triggered, read in UCI configuration files.
    - Pass sections off to appropriate handlers (interface, etc.).
    - Perform some validation (check for required options).
    - Emit commands (start/stop daemon, ip, iw, etc.) into a queue.
    - Issue commands, maybe rollback on failure.
    - Update known state of the system.

Reference:
https://github.com/cocagne/txdbus/blob/master/doc/tutorial.asciidoc
http://excid3.com/blog/an-actually-decent-python-dbus-tutorial/
"""

from twisted.internet import reactor, defer
from txdbus import client, objects, error
from txdbus.interface import DBusInterface, Method

bus_name = "org.paradrop"
service_name = "org.paradrop.config"
service_path = "/pdconfig"


class ConfigServiceDbus(objects.DBusObject):
    dbusInterfaces = [
        DBusInterface(service_name,
                      Method("Reload", arguments="s", returns="s"),
                      Method("ReloadAll", returns="s"),
                      Method("Test", returns="b"),
                      Method("UnloadAll", returns="b"),
                      Method("WaitSystemUp", returns="s"))
    ]

    def __init__(self, configManager):
        super(ConfigServiceDbus, self).__init__(service_path)
        self.configManager = configManager

    def dbus_Reload(self, name):
        return self.configManager.loadConfig(name)

    def dbus_ReloadAll(self):
        return self.configManager.loadConfig()

    def dbus_Test(self):
        return True

    def dbus_UnloadAll(self):
        return self.configManager.unload()

    def dbus_WaitSystemUp(self):
        return self.configManager.waitSystemUp()
