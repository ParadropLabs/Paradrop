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


class MockUpdate(object):
    pass


def writeTempFile(data):
    """
    Write data to a temporary file and return path to that file.
    """
    fd, path = tempfile.mkstemp()
    os.write(fd, data)
    os.close(fd)
    return path
