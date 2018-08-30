class ParadropConnectionError(Exception):
    """
    This exception indicates a connection failure to one of our API servers.

    It is subclassed by ControllerConnectionError and
    NodeConnectionError so that the UI code can distinguish the error
    types. Otherwise, the contents are essentially the same.
    """
    def __init__(self, message, request, target):
        super(ParadropConnectionError, self).__init__(message)
        self.target = target


class ControllerConnectionError(ParadropConnectionError):
    """
    This exception indicates a connection failure to a controller.
    """
    pass


class NodeConnectionError(ParadropConnectionError):
    """
    This exception indicates a connection failure to a node.
    """
    pass
