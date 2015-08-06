from pdtools.lib import output


def testPdtoolsImportable():
    import pdtools


def test_subscriptionWorks():
    output.out.startLogging(stealStdio=False, printToConsole=True)

    class Sub(object):

        def __init__(self):
            self.last = None

        def subscriber(self, a):
            self.last = a
        # last = a

    s = Sub()

    # Can subscribe
    output.out.addSubscriber(s.subscriber)
    output.out.info('Something')

    assert s.last is not None

    # Can unsubscribe
    s.last = None
    output.out.removeSubscriber(s.subscriber)
    output.out.info('Something')

    assert s.last is None
