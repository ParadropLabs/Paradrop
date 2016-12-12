"""
This module listens for messages from unix socket and triggers reloading of configuration files.
This module is the service side of the implementation.
If you want to issue reload commands to the service, see the client-rpc.py file instead.

Operation:
    - When triggered, read in UCI configuration files.
    - Pass sections off to appropriate handlers (interface, etc.).
    - Perform some validation (check for required options).
    - Emit commands (start/stop daemon, ip, iw, etc.) into a queue.
    - Issue commands, maybe rollback on failure.
    - Update known state of the system.

"""

from twisted.internet import reactor, defer
from txmsgpackrpc.server import MsgpackRPCServer


socket_path = '/run/paradrop.socket'

class ConfigServiceRpc(MsgpackRPCServer):

    def __init__(self, configManager):
        MsgpackRPCServer.__init__(self)
        self.configManager = configManager

    @defer.inlineCallbacks
    def remote_Reload(self, name):
        yield self.configManager.loadConfig(name)

    @defer.inlineCallbacks
    def remote_ReloadAll(self):
        yield self.configManager.loadConfig()

    @defer.inlineCallbacks
    def remote_Test(self):
        yield True

    @defer.inlineCallbacks
    def remote_UnloadAll(self):
        yield self.configManager.unload()

    @defer.inlineCallbacks
    def remote_WaitSystemUp(self):
        yield self.configManager.waitSystemUp()
