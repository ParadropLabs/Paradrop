'''
Wamp utility methods.
'''

from autobahn.twisted import wamp, websocket
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.types import ComponentConfig
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.ssl import ClientContextFactory

from . import nexus
from .output import out


# pylint: disable=inconsistent-mro
class BaseClientFactory(websocket.WampWebSocketClientFactory, ReconnectingClientFactory):
    # factor and jitter are two variables that control the exponential backoff.
    # The default values in ReconnectingClientFactory seem reasonable.
    initialDelay = 1
    maxDelay = 60

    def clientConnectionFailed(self, connector, reason):
        out.info("Connection failed with reason: " + str(reason))
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def clientConnectionLost(self, connector, reason):
        out.info("Connection lost with reason: " + str(reason))
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)


class BaseSessionFactory(wamp.ApplicationSessionFactory):
    def __init__(self, config, deferred=None):
        super(BaseSessionFactory, self).__init__(config)
        self.dee = deferred

    def __call__(self, *args, **kwargs):
        sess = super(BaseSessionFactory, self).__call__(*args, **kwargs)
        sess.dee = self.dee
        return sess


class BaseSession(ApplicationSession):

    """ Temporary base class for crossbar implementation """

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config=config)
        self.pdid = config.extra

    @classmethod
    def start(klass, address, pdid, realm='paradrop', start_reactor=False,
              debug=False, extra=None, reconnect=True):
        '''
        Creates a new instance of this session and attaches it to the router
        at the given address and realm.

        reconnect: The session will attempt to reconnect on connection failure
            and continue trying indefinitely.
        '''
        # Enable log messages of autobahn for debugging
        #import txaio
        #txaio.start_logging()

        dee = Deferred()

        component_config = ComponentConfig(realm=u''+realm, extra=u''+pdid)
        session_factory = BaseSessionFactory(config=component_config, deferred=dee)
        session_factory.session = klass

        transport_factory = BaseClientFactory(session_factory, url=address)
        if not reconnect:
            transport_factory.maxRetries = 0
        transport_factory.setProtocolOptions(autoPingInterval=8., autoPingTimeout=4.,)
        context_factory = ClientContextFactory()
        websocket.connectWS(transport_factory, context_factory)

        if start_reactor:
            reactor.run()

        return dee

        # This the the recommended way to start the WAMP component,
        # but it is friendly to customize the component
        #runner = ApplicationRunner(url=u''+address, realm=u''+realm)
        #return runner.run(klass, start_reactor=start_reactor, auto_reconnect=reconnect)

    def leave(self):
        # Do not retry if explicitly asked to leave.
        self._transport.factory.maxRetries = 0
        nexus.core.session = None
        nexus.core.wamp_connected = False
        super(BaseSession, self).leave()

    @inlineCallbacks
    def onJoin(self, details):
        out.info(str(self.__class__.__name__) + ' crossbar session connected')

        # Update global session reference.  It's hacky, but we do the import
        # here to solve the circular import problem.  TODO Refactor.
        nexus.core.session = self
        nexus.core.wamp_connected = True

        # Reset exponential backoff timer after a successful connection.
        self._transport.factory.resetDelay()

        # Inform whoever created us that the session has finished connecting.
        # Useful in situations where you need to fire off a single call and not a
        # full wamplet
        if self.dee is not None:
            yield self.dee.callback(self)

    ###################################################
    # Overridden CX interaction methods
    ###################################################

    '''
    Note: this first set of methods have all the REAL implemnetion of caller identification:
    the caller's information is always passed along for every call. In the crossbar way of doing
    things, however, whats passed along is a session id and not our pdid.

    The second set of methods is temporary in that it manually passes the
    current sessions' pdid. This is not secure, but will have to do for now in the
    absence of crossbar router changes.
    '''

    def publish(self, topic, *args, **kwargs):
        # kwargs['options'] = PublishOptions(disclose_me=True)
        args = (self.pdid,) + args
        topic = _prepend(self.pdid, topic)
        # out.info('cxbr: (%s) publish (%s)' % (self.pdid, topic,))
        return ApplicationSession.publish(self, topic, *args, **kwargs)

    def subscribe(self, handler, topic=None, options=None):
        topic = _prepend(self.pdid, topic)
        out.info('cxbr: (%s) subscribe (%s)' % (self.pdid, topic,))
        return ApplicationSession.subscribe(self, handler, topic=topic, options=options)

    def call(self, procedure, *args, **kwargs):
        # kwargs['options'] = CallOptions(disclose_me=True)
        args = (self.pdid,) + args
        procedure = _prepend(self.pdid, procedure)
        # out.info('cxbr: (%s) calling (%s)' % (self.pdid, procedure,))
        return ApplicationSession.call(self, procedure, *args, **kwargs)

    def register(self, endpoint, procedure=None, options=None):
        # options = RegisterOptions(details_arg='session')
        procedure = _prepend(self.pdid, procedure)
        out.info('cxbr: (%s) register (%s)' % (self.pdid, procedure,))
        return ApplicationSession.register(self, endpoint, procedure=procedure, options=options)

    ###################################################
    # Access to the original methods, without convenience modifiers
    ###################################################
    def stockPublish(self, topic, *args, **kwargs):
        return ApplicationSession.publish(self, u''+topic, *args, **kwargs)

    def stockSubscribe(self, handler, topic=None, options=None):
        return ApplicationSession.subscribe(self, handler, topic=u''+topic, options=options)

    def stockCall(self, procedure, *args, **kwargs):
        return ApplicationSession.call(self, u''+procedure, *args, **kwargs)

    def stockRegister(self, endpoint, procedure=None, options=None):
        return ApplicationSession.register(self, endpoint, procedure=u''+procedure, options=options)


def _prepend(pdid, topic):
    '''
    In order to make subscription and execution code cleaner, this method automatically
    injects this classes pdid to the end of any publish or register call.

    The topic is also converted to a unicode string.
    No consideration is given to 'valid' topics-- thats on you.
    '''
    return u'' + topic + '.' + pdid
