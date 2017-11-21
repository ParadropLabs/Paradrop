import json
import os

from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredQueue
from twisted.internet.protocol import ClientFactory, ConnectedDatagramProtocol

from paradrop.base.output import out


class HostapControlProtocol(ConnectedDatagramProtocol):
    """
    Protocol for hostapd control interface.

    There are two modes of operation depending on the command argument:
    1. If command is None, the protocol connects to the control interface and
    saves all detected events to the queue.
    2. If command is not None, the protocol connects to the control interface,
    sends the command, and only saves messages related to the command
    execution.
    """
    # Number of instances created, used for creating unique paths.
    counter = 0

    def __init__(self, queue, command=None):
        self.queue = queue
        self.command = command

        self.instance = HostapControlProtocol.counter
        HostapControlProtocol.counter += 1

    def datagramReceived(self, datagram):
        obj = {}

        # If the line contains any equal signs, interpret it as a list of
        # key-value pairs. Otherwise, interpret it as a single message, e.g.
        # "OK".
        if "=" in datagram:
            for line in datagram.split("\n"):
                # There might be an equal sign in the value, so limit the
                # number of splits to one.
                words = line.split("=", 1)
                if len(words) < 2:
                    continue
                obj[words[0]] = words[1]
        else:
            obj['message'] = datagram.rstrip()

        self.queue.put(obj)

        # If this connection was opened for the purpose of executing a command,
        # then we are done and can close the connection.
        if self.command is not None:
            self.transport.loseConnection()

    def startProtocol(self):
        if self.command is not None:
            self.transport.write(self.command)

    def bindAddress(self):
        """
        Choose a path for the client side of the socket.

        This should be unique to avoid errors.
        - Use the tmp directory, so that they are sure to be cleaned up.
        - Use the PID for uniqueness if the daemon is restarted.
        - Use the counter for uniqueness across multiple requests.
        """
        return "/tmp/hostapd-{}-{}.sock".format(os.getpid(), self.instance)


def connect(address):
    queue = DeferredQueue()
    protocol = HostapControlProtocol(queue)
    reactor.connectUNIXDatagram(address, protocol, bindAddress=protocol.bindAddress())
    return queue


def execute(address, command):
    queue = DeferredQueue()
    protocol = HostapControlProtocol(queue, command=command)
    reactor.connectUNIXDatagram(address, protocol, bindAddress=protocol.bindAddress())
    return queue.get()
