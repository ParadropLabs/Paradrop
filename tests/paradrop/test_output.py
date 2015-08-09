import os
import shutil

from pdtools.lib import output

PATH = os.getcwd() + '/TESTLOGS'


def setup():
    assert not os.path.exists(PATH)
    os.makedirs(PATH)

    # mocks = {
    #     'log':'{"package":"pdfcd","timestamp":1437511829.055573,"extra":{"details":"floating print statement"},"module":"server","owner":"UNSET","message":"None","type":"VERBOSE","line":247,"pdid":"pd.damouse.example"}\n{"package":"pdfcd","timestamp":1437511829.05581,"extra":{},"module":"server","owner":"UNSET","message":"Establishing API server%2C port%3A 14321","type":"INFO","line":264,"pdid":"pd.damouse.example"}\n{"package":"lib","timestamp":1437511829.056349,"extra":{},"module":"output","owner":"UNSET","message":"Site starting on 14321","type":"INFO","line":385,"pdid":"pd.damouse.example"}\n{"package":"lib","timestamp":1437511829.056546,"extra":{},"module":"output","owner":"UNSET","message":"Starting factory %3Ctwisted.web.server.Site instance at 0x7f80689039e0%3E","type":"INFO","line":385,"pdid":"pd.damouse.example"}\n{"package":"lib","timestamp":1437511830.974387,"extra":{},"module":"output","owner":"UNSET","message":"Received SIGINT%2C shutting down.","type":"INFO","line":385,"pdid":"pd.damouse.example"}\n{"package":"lib","timestamp":1437511830.975079,"extra":{},"module":"output","owner":"UNSET","message":"Asking file logger to close","type":"INFO","line":416,"pdid":"pd.damouse.example"}\n{"package":"paradrop","timestamp":1437519443.939309,"extra":{"details":"floating print statement"},"module":"main","owner":"UNSET","message":"Look%2C print statements are ok now%21","type":"VERBOSE","line":101,"pdid":"pd.damouse.example"}'
    # }

    # Make three testing files
    # for k, v in mocks.iteritems():

    # with open(path + '/log') as f:


def teardown():
    shutil.rmtree(PATH)


def test_subscriptionWorks():
    output.out.startLogging(filePath=PATH, stealStdio=False, printToConsole=True)

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


def test_getLogsOrdered():
    output.out.startLogging(filePath=PATH, stealStdio=False, printToConsole=True)
