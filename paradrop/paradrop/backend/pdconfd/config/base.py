import copy

class ConfigObject(object):
    nextId = 0
    typename = None
    options = []

    def __init__(self):
        self.id = ConfigObject.nextId
        ConfigObject.nextId += 1

        self.source = None
        self.name = "s{:08x}".format(self.id)
        self.comment = None
        self.dependents = set()

        # Will be a running list of commands executed by request of this config
        # object.
        self.executed = list()

        for option in self.options:
            setattr(self, option['name'], option['default'])

    def __hash__(self):
        return hash(self.getTypeAndName())

    def __str__(self):
        return "config {} {}".format(self.typename, self.name)

    def setup(self):
        """
        Finish object initialization.

        This is called after the config object is initialized will all of its
        options values filled in.  Override to do some preparation work before
        we start generating commands.
        """
        pass

    def addDependent(self, dep):
        self.dependents.add(dep)

    def commands(self, allConfigs):
        """
        Return a list of commands to execute.

        Each one is a Command object.
        """
        return []

    def copy(self):
        """
        Make a copy of the config object.

        The copy will receive the same name and option values.
        """
        other = self.__class__()

        other.source = self.source
        other.name = self.name
        other.comment = self.comment
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
        return (self.typename, self.name)

    def lookup(self, allConfigs, sectionType, sectionName, addDependent=True):
        """
        Look up a section by type and name.

        If addDependent is True (default), the current object will be added as
        a dependent of the found section.

        Will raise an exception if the section is not found.
        """
        config = allConfigs[(sectionType, sectionName)]
        if addDependent:
            config.addDependent(self)
        return config

    def undoCommands(self, allConfigs):
        """
        Return a list of commands to execute.

        Each one is a Command object.
        """
        return []

    def update(self, new, allConfigs):
        """
        Return a list of commands to update to new configuration.

        This is called when a new configuration is loaded with the same name
        but different options.  The default behavior is to revert the old
        configuration (by calling undoCommands) and apply the new configuration
        (by calling commands).  However, in certain cases that could be
        disruptive, so we can do incremental updates by overriding this
        function.

        Return None to go with default behavior (described above) or return
        a list of commands to perform the update.
        """
        return None

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
        obj = cls()
        obj.manager = manager
        obj.source = source
        obj.comment = comment

        if name is not None:
            obj.name = name

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
