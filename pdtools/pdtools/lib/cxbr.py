'''
Wamp utility methods. 
'''

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred


@inlineCallbacks
def cxCall(session):
    '''
    One shot crossbar utility method. 
    '''
    dee = Deferred()

    def maker(cfg):
        sess = session(cfg)
        sess.dee = dee
        return sess

    runner = ApplicationRunner("ws://127.0.0.1:8080/ws", u"crossbardemo")
    yield runner.run(maker, start_reactor=False)

    session = yield dee
    returnValue(session)
