class Service(object):
    """
    A service is a long-running process that provides chute functionality.
    """
    def __init__(self, chute, name):
        self.chute = chute
        self.name = name

    def get_container_name(self):
        if self.name is None:
            # name can be None for old-style single-service chutes where the
            # container name is expected to be the name of the chute.
            return self.chute.name
        else:
            return "{}-{}".format(self.chute.name, self.name)
