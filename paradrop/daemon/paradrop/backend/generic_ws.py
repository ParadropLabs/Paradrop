from autobahn.twisted.websocket import WebSocketServerProtocol
from twisted.internet import interfaces
from zope.interface import implementer


@implementer(interfaces.IConsumer)
@implementer(interfaces.IPushProducer)
class ProducerConsumerWsProtocol(WebSocketServerProtocol):
    """
    Generic producer/consumer websocket protocol.

    This protocol accepts data from any implementer of IPushProducer or
    IPullProducer and forwards it to the websocket connection.  It also reads
    data from the websocket connection and forwards it to any implementer of
    IConsumer.  Either of the consumer or producer sides are optional.
    """
    def __init__(self, consumer=None):
        WebSocketServerProtocol.__init__(self)
        self.connected = False
        self.producer = None
        self.streaming = True

        self.consumer = consumer
        self.paused = False

    def onClose(self, wasClean, code, reason):
        self.connected = False
        if self.producer is not None:
            self.producer.stopProducing()

    def onOpen(self):
        self.connected = True
        if self.producer is not None:
            self.producer.resumeProducing()

    def onMessage(self, payload, isBinary):
        if self.consumer is not None:
            self.consumer.write(payload)

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
        self.sendMessage(data)
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
            self.transport.stopProducing()
