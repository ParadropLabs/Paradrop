###################################################################
# Copyright 2013-2018 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import attr

from paradrop.base.exceptions import ServiceNotFound


@attr.s
class Chute(object):
    """
    This Chute class provides the internal representation of a Paradrop chute.

    This class encapsulates the complex configuration details of a chute and
    provides a stable interface for the execution path even as the chute
    specification language evolves over time.

    The Chute class has minimal external dependencies, e.g. no dependency on
    the Docker API. Chute objects should be immutable, since they describe a
    desired software state at a fixed point in time.

    Args:
        name (str): The name of the chute.
        description (str): The human-friendly description of the chute.
        state (str): Desired run state of the chute ("running", "stopped").
        version (str): The version of the chute.
        config (dict): Configuration settings for the chute.
        environment (dict): Environment variables to set for all chute services.
    """
    STATE_INVALID = "invalid"
    STATE_DISABLED = "disabled"
    STATE_RUNNING = "running"
    STATE_FROZEN = "frozen"
    STATE_STOPPED = "stopped"

    description = attr.ib(default=None)
    name        = attr.ib(default=None)
    owner       = attr.ib(default=None)
    state       = attr.ib(default="running")
    version     = attr.ib(default=None)
    config      = attr.ib(default=attr.Factory(dict))
    environment = attr.ib(default=attr.Factory(dict))
    services    = attr.ib(default=attr.Factory(dict))
    web         = attr.ib(default=attr.Factory(dict))

    # The cache as a working storage of intermediate values has been moved
    # to the update object. Here, we set the cache right before saving the
    # chute to disk so that the values can be retrieved with the chute
    # list.
    _cache      = attr.ib(default=attr.Factory(dict))

    def __repr__(self):
        return "<Chute {} - {}>".format(self.name, self.state)

    def __str__(self):
        return "Chute:{}".format(self.name)

    def isRunning(self):
        """
        Check if the chute is supposed to be running.
        """
        return self.state == Chute.STATE_RUNNING

    def isValid(self):
        """Return True only if the Chute object we have has all the proper things defined to be in a valid state."""
        if (not self.name or len(self.name) == 0):
            return False
        return True

    def getCache(self, key):
        """
        Get a value from the cache or None if it does not exist.
        """
        return self._cache.get(key, None)

    def getCacheContents(self):
        """
        Get the contents of the cache as a dictionary.
        """
        return self._cache

    def setCache(self, key, value):
        """
        Set a value in the cache.

        Deprecated: Most of the cache functionality has been moved to the
        Update object because they are values that are used as temporary
        storage between one update step and the following steps. However, there
        are a few instances of cache values that we do still read from chute
        storage. Any calls to the getCache method throughout the project are
        still depending on this functionality, so we have corresponding calls
        to setCache that ensure the required information is present in the
        chute cache and not just in the update cache. Eventually, we should
        remove this dependency either by using a less stateful design or by
        formalizing the process for storing persistent chute state, such as the
        networkInterfaces list.
        """
        self._cache[key] = value

    def updateCache(self, other):
        """
        Update the chute cache from another dictionary.
        """
        self._cache.update(other)

    def getConfiguration(self):
        """
        Get the chute's configuration object.
        """
        # TODO: Split metadata (e.g. name and version) from configuration data.
        # Currently, we do this by selectively copying from __dict__.  A
        # cleaner separation would require refactoring all the way through how
        # we create update objects.
        return self.config

    def getHostConfig(self):
        """
        Get the chute's host_config options for Docker.

        Returns an empty dictionary if there is no host_config setting.
        """
        return self.config.get('host_config', {})

    def getWebPort(self):
        """
        Get the port configured for the chute's web server.

        Returns port (int) or None if no port is configured.
        """
        try:
            return int(self.config['web']['port'])
        except:
            return None

    def inherit_attributes(self, other):
        """
        Inherit attributes from another version of the chute.

        If any settings are None or missing in this chute but present in the
        other version, they will be copied over. The return value is a
        dictionary containing changes that were applied.
        """
        changes = {}
        for attr_name in ["name", "description", "state", "version"]:
            if getattr(self, attr_name, None) is None:
                other_value = getattr(other, attr_name, None)
                if other_value is not None:
                    setattr(self, attr_name, other_value)
                    changes[attr_name] = other_value
        return changes

    def add_service(self, service):
        """
        Add a service to the chute.
        """
        self.services[service.name] = service

    def create_specification(self):
        """
        Create a new chute specification from the existing chute.

        This is a completely clean copy of all information necessary to rebuild
        the Chute object. It should contain only primitive types, which can
        easily be serialized as JSON or YAML.
        """
        def no_privates(a, _):
            return not a.name.startswith('_')

        return attr.asdict(self, filter=no_privates)

    def get_default_service(self):
        """
        Get one of the chute's services designated as the default one.

        This is more for convenience with existing API functions where the
        caller did not need to specify a service because prior to 0.12.0,
        chutes could only have one Docker container. We use some heuristics
        such as the service's name is "main" to identify one of the services as
        the default.
        """
        if "main" in self.services:
            return self.services['main']

        # Sort by name and return the first one.
        name = min(self.services)
        return self.services[name]

    def get_environment(self):
        """
        Get the chute environment variables.

        These are defined by the developer or administrator and passed to all
        services that belong to the chute.
        """
        return getattr(self, "environment", {})

    def get_owner(self):
        """
        Get the name of the user who owns this installed chute.
        """
        return getattr(self, "owner", None)

    def get_service(self, name):
        """
        Get a service by name.
        """
        if name in self.services:
            return self.services[name]
        else:
            raise ServiceNotFound(name)

    def get_services(self):
        """
        Get a list of services installed by this chute.
        """
        return self.services.values()

    def get_web_port_and_service(self):
        """
        Get the port and Service object that provides this chutes web service.

        Returns a tuple containing the port number and Service object. Both
        values will be None if a web service is not configured.
        """
        port = self.web.get("port", None)
        if port is None:
            return None, None

        name = self.web.get("service", None)
        return port, self.get_service(name)
