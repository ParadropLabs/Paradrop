import os
import tempfile


class MockChute(object):
    def __init__(self, name="mock"):
        self.name = name

        self.cache = dict()

        self.IPs = list()
        self.SSIDs = list()
        self.staticIPs = list()

    def getCache(self, key):
        return self.cache.get(key, None)

    def setCache(self, key, value):
        self.cache[key] = value

    def getChuteIPs(self):
        return self.IPs

    def getChuteSSIDs(self):
        return self.SSIDs

    def getChuteStaticIPs(self):
        return self.staticIPs


class MockChuteStorage(object):
    def __init__(self):
        self.chuteList = list()

    def getChuteList(self):
        return self.chuteList


class MockPlans(object):
    def __init__(self):
        self.plans = list()

    def addPlans(self, priority, plans):
        self.plans.extend(plans)


class MockUpdate(object):
    def __init__(self, name="mock"):
        self.name = name
        self.plans = MockPlans()
        self.responses = list()


def call(func, *args, **kwargs):
    """
    Call a function with any arguments.
    """
    func(*args, **kwargs)


def do_nothing(*args, **kwargs):
    """
    Do nothing with any arguments.
    """
    pass


def make_dummy(retval):
    """
    Make a dummy function that always returns the given value.
    """
    return lambda *args, **kwargs: retval


def writeTempFile(data):
    """
    Write data to a temporary file and return path to that file.
    """
    fd, path = tempfile.mkstemp()
    os.write(fd, data)
    os.close(fd)
    return path
