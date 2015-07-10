'''
Client-side tools for communicating with a server using RPC
'''

from twisted.web.xmlrpc import Proxy


class RpcClient:

    '''
    Remote client RPC wrapper. Translates seemingly local calls
    into remote RPC calls.

    Will aleays return deferreds
    '''

    def __init__(self, urlAndPort):
        self.proxy = Proxy(urlAndPort, allowNone=True)

    def __getattr__(self, item):
        def wrap(*args):
            return self.proxy.callRemote(item, *args)

        return wrap
