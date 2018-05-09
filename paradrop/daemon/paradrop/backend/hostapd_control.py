import json
import os

from autobahn.twisted.websocket import WebSocketServerFactory
from twisted.internet import interfaces, reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ConnectedDatagramProtocol
from zope.interface import implementer

from .generic_ws import ProducerConsumerWsProtocol


@implementer(interfaces.IConsumer)
@implementer(interfaces.IPushProducer)
class HostapdControlProtocol(ConnectedDatagramProtocol):
    """
    Protocol for hostapd control interface.

    There are two modes of operation depending on the command argument:
    1. If command is None, the protocol connects to the control interface and
    saves all detected events to the queue.
    2. If command is not None, the protocol connects to the control interface,
    sends the command, and only saves messages related to the command
    execution.

    Reference:
    https://w1.fi/wpa_supplicant/devel/ctrl_iface_page.html
    """
    # Number of instances created, used for creating unique paths.
    counter = 0

    def __init__(self, consumer=None, command=None, emit_json=True):
        self.consumer = consumer
        self.command = command
        self.emit_json = emit_json

        self.producer = None
        self.streaming = False

        self.connected = False
        self.paused = False

        self.instance = HostapdControlProtocol.counter
        HostapdControlProtocol.counter += 1

    def datagramReceived(self, datagram):
        output = datagram

        if self.emit_json:
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
            output = json.dumps(obj)

        if self.consumer is not None:
            self.consumer.write(output)

    def startProtocol(self):
        self.connected = True
        if self.command is not None:
            self.transport.write(self.command)

    def bindAddress(self):
        """
        Choose a path for the client side of the UNIX socket.

        This should be unique to avoid errors.
        - Use the tmp directory, so that they are sure to be cleaned up.
        - Use the PID for uniqueness if the daemon is restarted.
        - Use the counter for uniqueness across multiple requests.
        """
        return "/tmp/hostapd-{}-{}.sock".format(os.getpid(), self.instance)

    #
    # IConsumer interface
    #

    def registerProducer(self, producer, streaming):
        self.producer = producer
        self.streaming = streaming

        # We are ready to receive data from the producer when the websocket
        # connection is open.
        if self.connected:
            producer.resumeProducing()
        else:
            producer.pauseProducing()

    def unregisterProducer(self):
        self.producer = None

    def write(self, data):
        self.transport.write(data)
        if not self.streaming:
            self.producer.resumeProducing()

    #
    # IPushProducer interface
    #

    def pauseProducing(self):
        self.paused = True
        if self.connected:
            self.transport.pauseProducing()

    def resumeProducing(self):
        self.paused = False
        if self.connected:
            self.transport.resumeProducing()

    def stopProducing(self):
        if self.connected:
            self.transport.loseConnection()


@implementer(interfaces.IConsumer)
class SingleItemConsumer(object):
    """
    Consumer that accepts a single item from a producer.

    This consumer waits for a single item from the producer and passes it to a
    Deferred object.
    """
    def __init__(self, deferred):
        self.deferred = deferred
        self.producer = None

    def registerProducer(self, producer, streaming):
        self.producer = producer
        producer.resumeProducing()

    def unregisterProducer(self):
        self.producer = None

    def write(self, data):
        self.deferred.callback(data)
        self.producer.stopProducing()


class HostapdControlWSFactory(WebSocketServerFactory):
    def __init__(self, control_interface):
        WebSocketServerFactory.__init__(self)
        self.control_interface = control_interface

    def buildProtocol(self, address):
        ws = ProducerConsumerWsProtocol()
        ws.factory = self

        control = HostapdControlProtocol(emit_json=False)
        reactor.connectUNIXDatagram(self.control_interface, control,
                bindAddress=control.bindAddress())

        ws.consumer = control
        control.consumer = ws

        ws.registerProducer(control, True)
        control.registerProducer(ws, True)

        return ws


def execute(address, command):
    deferred = Deferred()
    consumer = SingleItemConsumer(deferred)

    protocol = HostapdControlProtocol(consumer, command=command)
    consumer.registerProducer(protocol, True)

    reactor.connectUNIXDatagram(address, protocol, bindAddress=protocol.bindAddress())
    return deferred
