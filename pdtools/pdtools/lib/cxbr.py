'''
Wamp utility methods. 
'''

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from autobahn.wamp.types import RegisterOptions, SubscribeOptions, CallOptions, PublishOptions


class BaseSession(ApplicationSession):

    """ Temporary base class for crossbar implementation """

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config=config)
        self.pdid = config.extra

    @classmethod
    def start(klass, address, realm, pdid, start_reactor=False, debug=False):
        '''
        Creates a new instance of this session and attaches it to the router
        at the given address and realm. The pdid is set manually now since we trust
        clients. Excessively.
        '''
        dee = Deferred()

        def maker(cfg):
            sess = klass(cfg)
            sess.dee = dee
            return sess

        runner = ApplicationRunner(address, u'' + realm, extra=pdid, debug_wamp=debug, debug=debug,)
        runner.run(klass, start_reactor=start_reactor)

    @inlineCallbacks
    def onJoin(self, details):
        print 'Session Joined'
        yield

        # Inform whoever created us that the session has finished connecting.
        # Useful in situations where you need to fire off a single call and not a
        # full wamplet
        if self.dee is not None:
            yield self.dee.callback(self)

    def pdRegister(self, name, *args, **kwargs):
        '''
        Very quick and dirty RPC registration that prepends the currently set PDID
        to the given method name.

        Incomplete. 
        '''

        if self.pdid is None:
            raise Exception("No PDID set! Cannot register!")

        ApplicationSession.register()

    # def onDisconnect(self):
    # print "disconnected"
    #     reactor.stop()

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

    # def publish(self, topic, *args, **kwargs):
    #     kwargs['options'] = PublishOptions(disclose_me=True)
    #     return ApplicationSession.publish(self, topic, *args, **kwargs)

    # def subscribe(self, handler, topic=None, options=None):
    #     options = SubscribeOptions(details_arg='details')
    #     return ApplicationSession.subscribe(self, handler, topic=topic, options=options)

    # def call(self, procedure, *args, **kwargs):
    #     kwargs['options'] = CallOptions(disclose_me=True)
    #     return ApplicationSession.call(self, procedure, *args, **kwargs)

    # def register(self, endpoint, procedure=None, options=None):
    #     options = RegisterOptions(details_arg='details')
    #     return ApplicationSession.register(self, endpoint, procedure=procedure, options=options)

    def publish(self, topic, *args, **kwargs):
        # kwargs['options'] = PublishOptions(disclose_me=True)
        args = (self.pdid,) + args
        return ApplicationSession.publish(self, topic, *args, **kwargs)

    def subscribe(self, handler, topic=None, options=None):
        # options = SubscribeOptions(details_arg='details')
        return ApplicationSession.subscribe(self, handler, topic=topic, options=options)

    def call(self, procedure, *args, **kwargs):
        # kwargs['options'] = CallOptions(disclose_me=True)
        args = (self.pdid,) + args
        return ApplicationSession.call(self, procedure, *args, **kwargs)

    def register(self, endpoint, procedure=None, options=None):
        # options = RegisterOptions(details_arg='session')
        return ApplicationSession.register(self, endpoint, procedure=procedure, options=options)


@inlineCallbacks
def cxCall(session, address, realm, extra=None):
    '''
    One shot crossbar utility method. Creates a session object and starts it,
    returns a deferred that contains the object. 

    Take a session and returns once the session has connected. 
    '''

    # WAMP ApplicationSession is already using 'd,' so went with something a little more creative
    dee = Deferred()

    def maker(cfg):
        sess = session(cfg)
        sess.dee = dee
        return sess

    runner = ApplicationRunner(address, realm, extra=extra, debug_wamp=False, debug=False,)
    yield runner.run(maker, start_reactor=False)

    session = yield dee
    returnValue(session)
