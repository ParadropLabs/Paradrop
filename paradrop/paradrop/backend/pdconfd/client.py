import threading

from twisted.internet import reactor, defer
from txdbus import client, error

from main import service_name, service_path

@defer.inlineCallbacks
def callDeferredMethod(method, *args):
    try:
        conn = yield client.connect(reactor, busAddress="system")
        robj = yield conn.getRemoteObject(service_name, service_path)
        result = yield robj.callRemote(method, *args)
        defer.returnValue(result)
    except error.DBusException as e:
        print("D-Bus error: {}".format(e))

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

def reloadAll():
    d = callDeferredMethod("ReloadAll")
    blocking = Blocking(d)
    return blocking.wait()

def reload(path):
    d = callDeferredMethod("Reload", path)
    blocking = Blocking(d)
    return blocking.wait()

def waitSystemUp():
    d = callDeferredMethod("WaitSystemUp")
    blocking = Blocking(d)
    return blocking.wait()
