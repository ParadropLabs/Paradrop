import os
import time
import shutil
import json

from pdtools.lib import output

PATH = os.getcwd() + '/TESTLOGS/'


def setup():
    os.makedirs(PATH)

    mockOut = {'extra': {}, 'owner': 'UNSET', 'message': 'Establishing API server, port: 14321', 'package': 'pdfcd', 'type': 'INFO', 'line': 272, 'module': 'server', 'pdid': 'pd.damouse.example'}
    
    days = [[mockOut] * 3 for x in range(3)]
    hour, day = 60 * 60, 24 * 60 * 60

    for i in range(0, len(days)):
        name = output.LOG_NAME

        if i != 0:
            name += '.' + time.strftime('%Y_%m_%d', time.localtime(time.time() - i * day))

        with open(PATH + name, 'w') as f:
            for k in range(0, len(days[i])):
                days[i][k]['timestamp'] = time.time() - i * day + k * hour

                d = json.dumps(days[i][k])
                f.write(d + '\n')

    output.out.startLogging(filePath=PATH, stealStdio=False, printToConsole=True)


def teardown():
    output.out.endLogging()
    shutil.rmtree(PATH)


def test_subscriptionWorks():
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


def test_logsOrdered():
    logs = output.out.getLogsSince(0)

    x = None

    assert len(logs) == 9

if __name__ == '__main__':
    try:
        setup()

        test_logsOrdered()
    finally:
        teardown()
        pass

    # from pdtools.lib import pdutils

    # dicts = [dict(a=1, b=2, c=3, d=4)] * 10000

    # with pdutils.Timer('Our conversion') as t:
    #     [pdutils.json2str(x) for x in dicts]

    # with pdutils.Timer('Native') as t:
    #     [json.dumps(x) for x in dicts]