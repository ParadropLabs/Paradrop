from twisted.internet import reactor, defer
from txdbus import client, error

from paradrop.base.lib.output import out

from .configservice_dbus import bus_name, service_path


@defer.inlineCallbacks
def callDeferredMethodDbus(method, *args):
    try:
        conn = yield client.connect(reactor, busAddress="system")
        robj = yield conn.getRemoteObject(bus_name, service_path)
        result = yield robj.callRemote(method, *args)
        defer.returnValue(result)
    except error.DBusException as e:
        out.err("D-Bus error: {}".format(e))

