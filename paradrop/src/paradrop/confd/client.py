import threading
from twisted.internet import reactor, defer

from paradrop.base.output import out

from .main import configManager
from .client_dbus import callDeferredMethodDbus
from .client_rpc import callDeferredMethodRpc

class Blocking(object):

    """
    Uses threading.Event to implement blocking on a twisted deferred object.

    The wait method will wait for its completion and return its result.
    """

    def __init__(self, deferred):
        self.event = threading.Event()
        self.result = None
        deferred.addCallback(self.unlock)

    def unlock(self, result):
        self.result = result
        self.event.set()

    def wait(self):
        # Try to detect if we are in the reactor main thread.  If we are,
        # blocking here will prevent unlock from ever being called.
        if threading.currentThread().getName() == "MainThread":
            raise Exception("Blocking in reactor main thread")
        self.event.wait()
        return self.result


def reloadAll(adapter=''):
    """
    Reload all files from the system configuration directory.

    This function blocks until the request completes.  On completion it returns
    a status string, which is a JSON list of loaded configuration sections with
    a 'success' field.  For critical errors such as failure to connect to the
    D-Bus service, it will return None.
    """
    if adapter == 'dbus':
        d = callDeferredMethodDbus("ReloadAll")
        blocking = Blocking(d)
        return blocking.wait()
    elif adapter == 'rpc':
        d = callDeferredMethodRpc("ReloadAll")
        blocking = Blocking(d)
        return blocking.wait()
    else:
        return configManager.loadConfig()


def reload(path, adapter=''):
    """
    Reload file(s) specified by path.

    This function blocks until the request completes.  On completion it returns
    a status string, which is a JSON list of loaded configuration sections with
    a 'success' field.  For critical errors such as failure to connect to the
    D-Bus service, it will return None.
    """
    if adapter == 'dbus':
        d = callDeferredMethodDbus("Reload", path)
        blocking = Blocking(d)
        return blocking.wait()
    elif adapter == 'rpc':
        d = callDeferredMethodRpc("Reload", path)
        blocking = Blocking(d)
        return blocking.wait()
    else:
        return configManager.loadConfig(path)


def waitSystemUp(adapter=''):
    """
    Wait for the configuration daemon to finish its first load.

    This function blocks until the request completes.  On completion it returns
    a status string, which is a JSON list of loaded configuration sections with
    a 'success' field.  For critical errors such as failure to connect to the
    D-Bus service, it will return None.
    """
    if adapter == 'dbus':
        d = callDeferredMethodDbus('WaitSystemUp')
        blocking = Blocking(d)
        return blocking.wait()
    elif adapter == 'rpc':
        d = callDeferredMethodRpc('WaitSystemUp')
        blocking = Blocking(d)
        return blocking.wait()
    else:
        return configManager.waitSystemUp()
