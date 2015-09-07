import copy

class ConfigObject(object):
    nextId = 0
    typename = None
    options = []

    # Priorities to ensure proper interleaving of commands.
    # Revert commands should use negated value.
    PRIO_CREATE_IFACE = 20
    PRIO_CONFIG_IFACE = 40
    PRIO_START_DAEMON = 60

    def __init__(self, name=None):
        self.id = ConfigObject.nextId
        ConfigObject.nextId += 1

        self.source = None
        self.name = name
        self.comment = None

        self.parents = set()
        self.dependents = set()

        # name is the externally visible name, e.g. "lan" in 
        # "config interface lan".  name is None for anonymous sections,
        # e.g. "config wifi-iface".
        #
        # internalName is used for identifying config objects and must
        # always be defined.  For anonymous sections, we generate a unique
        # name from id.
        if name is None:
            self.internalName = "s{:08x}".format(self.id)
        else:
            self.internalName = name

        # Will be a running list of commands executed by request of this config
        # object.
        self.executed = list()

        for option in self.options:
            setattr(self, option['name'], option['default'])

    def __hash__(self):
        return hash(self.getTypeAndName())

    def __str__(self):
        if self.name is None:
            return "config {}".format(self.typename)
        else:
            return "config {} {}".format(self.typename, self.name)

    def setup(self):
        """
        Finish object initialization.

        This is called after the config object is initialized will all of its
        options values filled in.  Override to do some preparation work before
        we start generating commands.
        """
        pass

    def copy(self):
        """
        Make a copy of the config object.

        The copy will receive the same name and option values.
        """
        other = self.__class__()

        other.source = self.source
        other.name = self.name
        other.comment = self.comment
        
        other.parents = self.parents.copy()
        other.dependents = self.dependents.copy()

        for option in self.options:
            # We use copy here because it works with both the str- and
            # list-typed values.  Any lists are lists of strings, so
            # shallow-copy here is fine.
            copied = copy.copy(getattr(self, option['name']))
            setattr(other, option['name'], copied)

        # We should call setup on a new config object after all of the option
        # values are filled in.
        other.setup()

        return other

    def getTypeAndName(self):
        """
        Return tuple (section type, section name).
        """
        return (self.typename, self.internalName)

    def lookup(self, allConfigs, sectionType, sectionName, addDependent=True):
        """
        Look up a section by type and name.

        If addDependent is True (default), the current object will be added as
        a dependent of the found section.

        Will raise an exception if the section is not found.
        """
        config = allConfigs[(sectionType, sectionName)]
        if addDependent:
            self.parents.add(config)
            config.dependents.add(self)
        return config

    def optionsMatch(self, other):
        """
        Test equality of config sections by comparing option values.
        """
        if not isinstance(other, self.__class__):
            return False
        for opdef in self.options:
            if getattr(self, opdef['name']) != getattr(other, opdef['name']):
                return False
        return True

    #
    # The following methods (apply, revert, updateApply, and updateRevert)
    # are the most important for subclasses to override.
    #
    # These methods are expected to return a list of commands to make system
    # changes when the section is loaded, deleted, or modified.
    #
    # Here is the methods are used:
    #
    # 1. When a section is loaded for the first time (new), the apply method
    # is called to perform actions such as create an interface or firewall
    # rule.
    #
    # 2. When a section is unloaded or detected as removed from a configuration
    # file, the revert method is called to undo everything that was done by
    # apply (e.g. delete an interface or rule).
    #
    # 3. When a section is reloaded (and has changed) or one or more of its
    # dependencies have have changed, the two update methods are used.
    # updateRevert selectively reverts actions that were done by apply; it can
    # (and by default does) undo everything just as revert would.  Then
    # updateApply is called to apply any changes needed to bring the system to
    # the new required state.  A motivating example is in order.
    #
    # Suppose we have one or more APs running on a single WiFi device, and we
    # loaded a new configuration that changes the channel.  The default
    # behavior would be to call revert, then call apply.  Revert would not only
    # bring down the hostapd instances but also destroy the AP-mode interfaces.
    # The latter step, however, is not necessary to achieve a channel change,
    # and if written carefully, updateRevert and updateApply can achieve the
    # configuration change with less disruption.
    #

    def apply(self, allConfigs):
        """
        Return a list of commands to apply this configuration.

        Most subclasses will need to implement this function.

        Returns a list of (priority, Command) tuples.
        """
        return []

    def revert(self, allConfigs):
        """
        Return a list of commands to revert this configuration.

        Most subclasses will need to implement this function.

        Returns a list of (priority, Command) tuples.
        """
        return []

    def updateApply(self, new, allConfigs):
        """
        Return a list of commands to update to new configuration.

        Implementing this is optional for subclasses.  The default behavior is
        to call apply.

        Returns a list of (priority, Command) tuples.
        """
        return self.apply(allConfigs)

    def updateRevert(self, new, allConfigs):
        """
        Return a list of commands to (partially) revert the configuration.

        The implementation can be selective about what it reverts (e.g. do not
        delete an interface if we are only updating its IP address).  The
        default behavior is to call revert.

        Returns a list of (priority, Command) tuples.
        """
        return self.revert(allConfigs)

    @classmethod
    def build(cls, manager, source, name, options, comment):
        """
        Build a config object instance from the UCI section.

        Arguments:
        source -- file containing this configuration section
        name -- name of the configuration section
                If None, a unique name will be generated.
        options -- dictionary of options loaded from the section
        comment -- comment string or None
        """
        obj = cls(name)
        obj.manager = manager
        obj.source = source
        obj.comment = comment

        for opdef in cls.options:
            found = False

            if opdef['type'] == list:
                if "list" in options and opdef['name'] in options['list']:
                    value = options['list'][opdef['name']]
                    found = True
                elif opdef['name'] in options:
                    # Sometimes we expect a list but get a single value instead.
                    # Example:
                    #   ...
                    #   option network 'lan'
                    #   ...
                    # instead of
                    #   ...
                    #   list network 'lan'
                    #   ...
                    value = [options[opdef['name']]]
                    found = True
            elif opdef['type'] == bool:
                if opdef['name'] in options:
                    value = options[opdef['name']] != '0'
                    found = True
            else:
                if opdef['name'] in options:
                    value = opdef['type'](options[opdef['name']])
                    found = True

            if not found:
                if opdef['required']:
                    raise Exception("Missing required option {} in {}:{}:{}".format(
                        opdef['name'], source, cls.typename, name))
                else:
                    value = opdef['default']

            setattr(obj, opdef['name'], value)

        obj.setup()

        return obj

    @staticmethod
    def _assignPriority(config, assigned):
        """
        Recursively assign priorities to config objects based on dependencies.

        This is meant to be called by prioritizeConfigs.
        """
        if config in assigned:
            return assigned[config]

        priority = 0
        for parent in config.parents:
            pprio = ConfigObject._assignPriority(parent, assigned)
            if pprio >= priority:
                priority = pprio + 1

        assigned[config] = priority
        return priority

    @staticmethod
    def prioritizeConfigs(configs, reverse=False):
        """
        Assign priorities to config objects based on the dependency graph.

        Priority zero is assigned to all configs with no dependencies.
        
        priority(config1) > priority(config2) means config1 should be applied
        later than config2, and config1 should be reverted earlier than
        config2.  For configs with the same priority value, it is presumed
        that order does not matter.

        If reverse is True, the priorities are made negative so that traversing
        in increasing order gives the proper order for reverting.

        Returns a list of tuples (priority, config).  This format is suitable
        for heapq.
        """
        priorities = dict()
        for config in configs:
            ConfigObject._assignPriority(config, priorities)
        mult = -1 if reverse else 1
        return [(mult * prio, config) \
                for (config, prio) in priorities.iteritems()]
