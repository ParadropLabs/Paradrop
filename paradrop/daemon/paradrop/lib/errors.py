class ParadropException(Exception):
    pass

class ChuteNotFound(ParadropException):
    pass

class ChuteNotRunning(ParadropException):
    pass
