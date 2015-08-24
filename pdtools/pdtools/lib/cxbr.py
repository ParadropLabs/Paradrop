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

    # def onDisconnect(self):
    # print "disconnected"
    #     reactor.stop()


@inlineCallbacks
def cxCall(session, address, realm):
    '''
    One shot crossbar utility method. 

    Take a session and returns once the session has connected. 
    '''

    # WAMP ApplicationSession is already using 'd,' so went with something a little more creative
    dee = Deferred()

    def maker(cfg):
        sess = session(cfg)
        sess.dee = dee
        return sess

    runner = ApplicationRunner(address, realm)
    yield runner.run(maker, start_reactor=False)

    session = yield dee
    returnValue(session)
