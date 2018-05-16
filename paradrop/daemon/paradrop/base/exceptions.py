'''
Exceptions and their subclasses

TODO: Distill these down and make a heirarchy.
'''


class PdServerException(Exception):
    pass


class InteralException(Exception):
    pass


class AuthenticationError(PdServerException):
    pass


class InvalidCredentials(PdServerException):
    pass


class PdidError(PdServerException):
    pass


class PdidExclusionError(PdServerException):
    pass


class ModelNotFound(PdServerException):
    pass


class ParadropException(Exception):
    pass


class ChuteNotFound(ParadropException):
    pass


class ServiceNotFound(ParadropException):
    def __init__(self, name):
        message = "Service ({}) not found".format(name)
        super(ServiceNotFound, self).__init__(message)


class ChuteNotRunning(ParadropException):
    pass


class DeviceNotFoundException(ParadropException):
    pass
