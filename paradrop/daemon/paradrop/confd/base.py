import attr
import copy

import six


def interpretBoolean(s):
    """
    Interpret string as a boolean value.

    "0" and "False" are interpreted as False.  All other strings result in
    True.  Technically, only "0" and "1" values should be seen in UCI files.
    However, because of some string conversions in Python, we may encounter
    "False".
    """
    if s in ["0", "False"]:
        return False
    else:
        return True


class ConfigObject(object):
    nextId = 0
    typename = None
    options = []

    # Use to resolve conflicts in with old-style section naming.  maskable=True
    # means a section can be replaced when we are gathering the list of
    # ConfigObject subclasses.  We set maskable=False on network:interface so
    # that it receives precedence over qos:interface and old code continues to
    # work.
    maskable = True

    # Priorities to ensure proper interleaving of commands.
    # Revert commands should use negated value.
    PRIO_CREATE_IFACE = 20
    PRIO_CREATE_VLAN = 25
    PRIO_CONFIG_IFACE = 30
    PRIO_IPTABLES_TOP = 35
    PRIO_IPTABLES_ZONE = 36
    PRIO_IPTABLES_RULE = 37
    PRIO_CREATE_QDISC = 40
    PRIO_CONFIG_QDISC = 45
    PRIO_START_DAEMON = 60

    def __init__(self, name=None):
        self.id = ConfigObject.nextId
        ConfigObject.nextId += 1

        self.epoch = 0
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
            setattr(self, option.name, option.default)

    def __hash__(self):
        return hash(self.getTypeAndName())

    def __lt__(self, other):
        """
        Compare ConfigObject instances.

        Currently, it arbitrarily sorts based on the string form of the config
        section type and name (e.g. "config interface wlan0").
        """
        return str(self) < str(other)

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
            copied = copy.copy(getattr(self, option.name))
            setattr(other, option.name, copied)

        # We should call setup on a new config object after all of the option
        # values are filled in.
        other.setup()

        return other

    def dump(self):
        """
        Return full configuration section as a string.
        """
        result = "# internal id: s{:08x}\n".format(self.id)

        if self.name is None:
            result += "config {}".format(self.typename)
        else:
            result += "config {} {}".format(self.typename, self.name)
        if self.comment is not None:
            result += " #" + self.comment
        result += "\n"

        for opdef in self.options:
            value = getattr(self, opdef.name)
            if value is None:
                continue
            elif opdef.type == bool:
                result += "\toption {} '{}'\n".format(opdef.name, 1 * value)
            elif opdef.type == list:
                for v in value:
                    result += "\tlist {} '{}'\n".format(opdef.name, v)
            else:
                result += "\toption {} '{}'\n".format(opdef.name, value)

        return result

    def getName(self):
        """
        Return section name.

        Subclasses that do not have names (anonymous sections) should override
        this to return some other unique identifier such as an interface name.
        """
        return self.internalName

    def getTypeAndName(self):
        """
        Return tuple (section module, section type, section name).
        """
        return (self.getModule(), self.typename, self.getName())

    def lookup(self, allConfigs, sectionModule, sectionType, sectionName, addDependent=True):
        """
        Look up a section by type and name.

        If addDependent is True (default), the current object will be added as
        a dependent of the found section.

        Will raise an exception if the section is not found.
        """
        config = allConfigs[(sectionModule, sectionType, sectionName)]
        if addDependent:
            self.parents.add(config)
            config.dependents.add(self)
        return config

    def removeFromParents(self):
        """
        Remove this section from being tracked by its parents.

        Call this before discarding a configuration section so that later on,
        if the parent is updated, it doesn't try to update non-existent
        children.
        """
        for parent in self.parents:
            if self in parent.dependents:
                parent.dependents.remove(self)
        self.parents.clear()

    def findByType(self, allConfigs, module, typename, where={}):
        """
        Look up sections by type (generator).

        where: filter the returned results by checking option values.
        """
        for key in allConfigs.keys():
            if key[0] == module and key[1] == typename:
                # Skip this section if any of the option values do not match.
                if any(getattr(allConfigs[key], op, None) != where[op] for op in where):
                    continue
                yield allConfigs[key]

    def optionsMatch(self, other):
        """
        Test equality of config sections by comparing option values.
        """
        if not isinstance(other, self.__class__):
            return False
        for opdef in self.options:
            if getattr(self, opdef.name) != getattr(other, opdef.name):
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
        return new.apply(allConfigs)

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

            if opdef.type == list:
                if opdef.name in options:
                    value = options[opdef.name]
                    if not isinstance(value, list):
                        # Sometimes we expect a list but get a single value instead.
                        # Example:
                        #   ...
                        #   option network 'lan'
                        #   ...
                        # instead of
                        #   ...
                        #   list network 'lan'
                        #   ...
                        value = [value]
                    found = True
            elif opdef.type == bool:
                if opdef.name in options:
                    value = interpretBoolean(options[opdef.name])
                    found = True
            else:
                if opdef.name in options:
                    value = opdef.type(options[opdef.name])
                    found = True

            if not found:
                if opdef.required:
                    raise Exception("Missing required option {} in {}:{}:{}".format(
                        opdef.name, source, cls.typename, name))
                else:
                    value = opdef.default

            setattr(obj, opdef.name, value)

        # If this section specifies name as an option rather than in the header
        # line, update the name that will be used for comparison.
        if getattr(obj, "name", None) is not None and name is None:
            obj.internalName = obj.name

        obj.setup()

        return obj

    @classmethod
    def getModule(cls):
        """
        Get the module name (e.g. "dhcp", "wireless") for a ConfigObject class.
        """
        parts = cls.__module__.split(".")
        return parts[-1]

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
                for (config, prio) in six.iteritems(priorities)]


@attr.s(slots=True)
class ConfigOption(object):
    name = attr.ib(convert=str)
    type = attr.ib(default=str, validator=attr.validators.instance_of(type))
    required = attr.ib(convert=bool, default=False)
    default = attr.ib(default=None)
