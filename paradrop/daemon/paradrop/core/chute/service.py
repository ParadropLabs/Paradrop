import attr


@attr.s
class Service(object):
    """
    A service is a long-running process that provides chute functionality.
    """

    command     = attr.ib(default=None)
    dockerfile  = attr.ib(default=None)
    image       = attr.ib(default=None)
    name        = attr.ib(default=None)
    source      = attr.ib(default=None)
    type        = attr.ib(default="normal")
    build       = attr.ib(default=attr.Factory(dict))
    environment = attr.ib(default=attr.Factory(dict))
    interfaces  = attr.ib(default=attr.Factory(dict))
    requests    = attr.ib(default=attr.Factory(dict))

    # Reference to parent chute. This needs to be private (starts with an
    # underscore); otherwise, we have a circular reference problem when trying
    # to serialize the chute.
    _chute      = attr.ib(default=None)

    def create_specification(self):
        """
        Create a new service specification.

        This is a completely clean copy of all information necessary to rebuild
        the Service object. It should contain only primitive types, which can
        easily be serialized as JSON or YAML.
        """
        spec = {
            "type": self.type,
            "source": self.source,
            "image": self.image,
            "command": self.command,
            "build": self.build.copy(),
            "environment": self.environment.copy(),
            "interfaces": self.interfaces.copy(),
            "requests": self.requests.copy()
        }
        return spec

    def get_chute(self):
        """
        Get the chute to which this service belongs.
        """
        return self._chute

    def get_container_name(self):
        """
        Get the name for the service's container.

        This will be a combination of the chute name and the service name.
        """
        if self.name is None:
            # name can be None for old-style single-service chutes where the
            # container name is expected to be the name of the chute.
            return self._chute.name
        else:
            return "{}-{}".format(self._chute.name, self.name)

    def get_image_name(self):
        """
        Get the name of the image to be used.
        """
        # Light chute services have a shorthand image name like "python2" that
        # should not be interpreted as an actual Docker image name.
        if self.image is None or self.type == "light":
            return "{}:{}".format(self.get_container_name(), self._chute.version)
        else:
            return self.image
