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


class RiffleError(PdServerException):
    pass
