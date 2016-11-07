"""
This module listens for messages and triggers reloading of configuration files.
This module is the service side of the implementation.  If you want to
issue reload commands to the service, see the client.py file instead.

"""

from twisted.internet import reactor, defer
from paradrop.base.lib.output import out
from paradrop.lib import settings

from .config.manager import ConfigManager
from .configservice_dbus import ConfigServiceDbus
from .configservice_rpc import ConfigServiceRpc

configManager = None

@defer.inlineCallbacks
def listen(configManager, dbus):
    # Things get messy if pdconfd is restarted with running chutes.  Then it
    # will try to reconfigure the system.  One easy solution is to unload the
    # configuration before exiting.
    reactor.addSystemEventTrigger('before', 'shutdown',
                                  configManager.unload)

    # Now load all of the configuration for the first time.
    configManager.loadConfig()

    if dbus:
        service = ConfigServiceDbus(configManager)

        try:
            conn = yield client.connect(reactor, busAddress="system")
            conn.exportObject(service)
            yield conn.requestBusName(bus_name)
        except error.DBusException as e:
            out.warn("Failed to export DBus object: {}".format(e))
    else:
        service = ConfigServiceRpc(configManager)

        try:
            reactor.listenUNIX(ConfigServiceRpc.socket_path, service)
        except e:
            out.warn("Failed to listen on socket {}, {}".format(ConfigServiceRpc.socket_path, e))

def run_thread(execute=True, dbus=True):
    """
    Start pdconfd service as a thread.

    This function schedules pdconfd to run as a thread and returns immediately.
    """
    global configManager
    configManager = ConfigManager(settings.PDCONFD_WRITE_DIR, execute)
    reactor.callFromThread(listen, configManager, dbus)


def run_pdconfd(execute=True, dbus=True):
    """
    Start pdconfd daemon.

    This enters the pdconfd main loop.
    """
    global configManager
    configManager = ConfigManager(settings.PDCONFD_WRITE_DIR, execute)
    reactor.callWhenRunning(listen, configManager, dbus)
    reactor.run()
