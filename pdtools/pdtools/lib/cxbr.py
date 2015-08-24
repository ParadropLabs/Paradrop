'''
Wamp utility methods. 
'''

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred


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
