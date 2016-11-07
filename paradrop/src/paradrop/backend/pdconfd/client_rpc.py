from twisted.internet import reactor, defer
from txmsgpackrpc import client

from paradrop.base.lib.output import out

from .configservice_rpc import socket_path

@defer.inlineCallbacks
def callDeferredMethodRpc(method, *args):
    try:
        conn = yield client.connect_UNIX(socket_path, connectTimeout=5, waitTimeout=5)
        result = yield conn.createRequest(method, *args)
        defer.returnValue(result)
    except Exception as e:
        out.err("Unix sockets error: {}".format(e))
