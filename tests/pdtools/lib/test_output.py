import os
import time
import shutil
import json

from pdtools.lib import output

PATH = os.getcwd() + '/TESTLOGS/'
sourceLogs = None


def setup():
    '''
    Make three log files, the current one and two old ones. Each file is three days apart.
    Each log entry is one hour apart. The logs are ordered ascending in time as written.
    '''
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

    global sourceLogs
    sourceLogs = days

    output.out.startLogging(filePath=PATH, stealStdio=False, printToConsole=False)


def teardown():
    output.out.endLogging()
    shutil.rmtree(PATH)


def test_logsOrdered():
    logs = output.out.getLogsSince(0)

    last = None

    for x in logs:
        if x is not None:
            assert x['timestamp'] > last


def test_filterWorks():
    ''' Make sure we only get logs after the given time '''
    target = sourceLogs[1][1]['timestamp']
    logs = output.out.getLogsSince(target)

    for x in logs:
        assert x['timestamp'] > target


def test_returnType():
    logs = output.out.getLogsSince(0)

    for x in logs:
        assert type(x) is dict


###############################################################################
# Random inline testing
###############################################################################
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
