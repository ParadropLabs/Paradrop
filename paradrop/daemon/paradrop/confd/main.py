"""
This module listens for messages and triggers reloading of configuration files.
This module is the service side of the implementation.  If you want to
issue reload commands to the service, see the client.py file instead.

"""

from twisted.internet import reactor
from paradrop.base import settings

from .manager import ConfigManager

configManager = None

def listen(configManager):
    # Things get messy if pdconfd is restarted with running chutes.  Then it
    # will try to reconfigure the system.  One easy solution is to unload the
    # configuration before exiting.
    reactor.addSystemEventTrigger('before', 'shutdown',
                                  configManager.unload)

    # Now load all of the configuration for the first time.
    configManager.loadConfig()

def run_thread(execute=True):
    """
    Start pdconfd service as a thread.

    This function schedules pdconfd to run as a thread and returns immediately.
    """
    global configManager
    configManager = ConfigManager(settings.PDCONFD_WRITE_DIR, execute)
    reactor.callFromThread(listen, configManager)
