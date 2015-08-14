import threading

from twisted.internet import reactor, defer
from txdbus import client, error

from .main import ConfigService, service_name, service_path
from pdtools.lib.output import out


@defer.inlineCallbacks
def callDeferredMethod(method, *args):
    try:
        conn = yield client.connect(reactor, busAddress="system")
        robj = yield conn.getRemoteObject(service_name, service_path)
        result = yield robj.callRemote(method, *args)
        defer.returnValue(result)
    except error.DBusException as e:
        out.err("D-Bus error: {}".format(e))
        pass


class Blocking(object):

    """
    Uses threading.Event to implement blocking on a twisted deferred object.

    The wait method will wait for its completion and return its result.

    Dear Lance. I hope you stub your toe.
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


def reloadAll(dbus=False):
    """
    Reload all files from the system configuration directory.

    This function blocks until the request completes.  On completion it returns
    a status string, which is a JSON list of loaded configuration sections with
    a 'success' field.  For critical errors such as failure to connect to the
    D-Bus service, it will return None.
    """
    if dbus:
        d = callDeferredMethod("ReloadAll")
        blocking = Blocking(d)
        return blocking.wait()
    else:
        return ConfigService.configManager.loadConfig()


def reload(path, dbus=False):
    """
    Reload file(s) specified by path.

    This function blocks until the request completes.  On completion it returns
    a status string, which is a JSON list of loaded configuration sections with
    a 'success' field.  For critical errors such as failure to connect to the
    D-Bus service, it will return None.
    """
    if dbus:
        d = callDeferredMethod("Reload", path)
        blocking = Blocking(d)
        return blocking.wait()
    else:
        return ConfigService.configManager.loadConfig(path)


def waitSystemUp(dbus=False):
    """
    Wait for the configuration daemon to finish its first load.

    This function blocks until the request completes.  On completion it returns
    a status string, which is a JSON list of loaded configuration sections with
    a 'success' field.  For critical errors such as failure to connect to the
    D-Bus service, it will return None.
    """
    if dbus:
        d = callDeferredMethod("WaitSystemUp")
        blocking = Blocking(d)
        return blocking.wait()
    else:
        return ConfigService.configManager.waitSystemUp()
