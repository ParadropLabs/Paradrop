'''
Wamp utility methods. 
'''

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred


class BaseSession(ApplicationSession):

    """ Temporary base class for crossbar implementation """

    def __init__(self, config=None):
        ApplicationSession.__init__(self)
        self.config = config

    @inlineCallbacks
    def onJoin(self, details):
        # print 'Session Joined'
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

    runner = ApplicationRunner(address, realm, extra=extra)
    yield runner.run(maker, start_reactor=False)

    session = yield dee
    returnValue(session)
