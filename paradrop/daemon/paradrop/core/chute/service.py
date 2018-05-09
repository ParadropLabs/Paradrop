class Service(object):
    """
    A service is a long-running process that provides chute functionality.
    """

    def __init__(self,
                 chute=None,
                 name=None,
                 type="normal",
                 image=None,
                 dockerfile=None,
                 environment=None,
                 interfaces=None,
                 requests=None):
        self.chute = chute
        self.name = name

        self.type = type
        self.image = image
        self.dockerfile = dockerfile

        if environment is None:
            self.environment = {}
        else:
            self.environment = environment

        if interfaces is None:
            self.interfaces = {}
        else:
            self.interfaces = interfaces

        if requests is None:
            self.requests = {}
        else:
            self.requests = requests

    def get_container_name(self):
        """
        Get the name for the service's container.

        This will be a combination of the chute name and the service name.
        """
        if self.name is None:
            # name can be None for old-style single-service chutes where the
            # container name is expected to be the name of the chute.
            return self.chute.name
        else:
            return "{}-{}".format(self.chute.name, self.name)

    def get_image_name(self):
        """
        Get the name of the image to be used.
        """
        if self.image is not None:
            return self.image
        else:
            return "{}:{}".format(self.get_container_name(), self.chute.version)
