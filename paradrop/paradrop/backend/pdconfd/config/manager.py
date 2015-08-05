import heapq
import json
import os
import subprocess
import threading

from pdtools.lib.output import out
from paradrop.lib.utils import pdosq
from paradrop.lib.utils.uci import CONFIG_DIR, UCIConfig

# Import all of the modules defining section types, so that all subclasses of
# ConfigObject are known.
from . import dhcp
from . import firewall
from . import network
from . import wireless

from .base import ConfigObject


# Map of type names to the classes that handle them.
configTypeMap = dict()
for cls in ConfigObject.__subclasses__():
    configTypeMap[cls.typename] = cls


WRITE_DIR = "/var/run/pdconfd"
""" Directory for daemon configuration files, PID files, etc. """


def findConfigFiles(search=None):
    """
    Look for and return a list of configuration files.

    The behavior depends on whether the search argument is a file, a directory,
    or None.

    If search is None, return a list of files in the system config directory.
    If search is a file name (not a path), look for it in the working directory
    first, and the system directory second.  If search is a full path to a
    file, and it exists, then return that file.  If search is a directory,
    return the files in that directory.
    """
    if search is None:
        search = CONFIG_DIR

    files = list()
    if os.path.isfile(search):
        files.append(search)
    elif os.path.isdir(search):
        for fn in os.listdir(search):
            path = "{}/{}".format(search, fn)
            files.append(path)
    else:
        path = "{}/{}".format(CONFIG_DIR, search)
        if os.path.isfile(path):
            files.append(path)

    return files


def sortCommands(commands):
    """
    Return commands in order by priority.

    The input should be a list of command objects.  The output will be just the
    command part in order according to priority (ascending).  For ties, the
    order from the original list is maintained.
    """
    result = list()

    n = len(commands)
    for cmd in commands:
        # This math (n * prio + i) ensures that the commands are sorted by
        # priority level first, and by order added within each priority level.
        # This is functionally identical to keeping separate FIFO queues for
        # each priority level.  It is just nicer to deal with a single command
        # queue than a bunch of them.
        i = len(result)
        heapq.heappush(result, (n * cmd.priority + i, cmd))

    while len(result) > 0:
        prio, cmd = heapq.heappop(result)
        yield cmd


class ConfigManager(object):

    def __init__(self, writeDir=WRITE_DIR):
        self.writeDir = writeDir

        # Make sure directory exists.
        pdosq.makedirs(writeDir)

        self.previousCommands = list()
        self.currentConfig = dict()
        self.nextSectionId = 0

        # Number of objects requiring IP forwarding.
        # If >0, we need to enable system-wide.
        # If ==0, we can probably disable.
        self.forwardingCount = 0

        # Allow threads to wait for first load to complete.  This will be set
        # after the first load completes and will remain set thereafter.
        self.systemUp = threading.Event()

    def changingSet(self, files):
        """
        Return the sections from the current configuration that may have
        changed.

        This checks which sections from the current configuration came from
        files in the given file list.  These are sections that may be changed
        or removed when we reload the files.
        """
        out = set()
        files = set(files)
        for config in self.currentConfig.values():
            if config.source in files:
                out.add(config)
        return out

    def getPreviousCommands(self):
        """
        Get the most recent command list.
        """
        return sortCommands(self.previousCommands)

    def execute(self, commands):
        for cmd in sortCommands(commands):
            cmd.execute()

    def findMatchingConfig(self, config, byName=False):
        """
        Check the current config for an identical section.

        Returns the matching object or None.
        """
        # First try by name (faster).
        key = config.getTypeAndName()

        if key in self.currentConfig:
            oldConfig = self.currentConfig[key]
            if byName:
                return oldConfig
            if config.optionsMatch(oldConfig):
                return oldConfig

        # Loop over them and check by content.
        for oldConfig in self.currentConfig.values():
            if config.optionsMatch(oldConfig):
                return oldConfig

        return None

    def loadConfig(self, search=None, execute=True):
        """
        Load configuration files and apply changes to the system.

        We process the configuration files in sections.  Each section
        corresponds to an interface, firewall rule, DHCP server instance, etc.
        Each time we reload configuration files after the initial time, we
        check for changes against the current configuration.  Here is the
        decision tree for handling differences in the newly loaded
        configuration vs. the existing configuration:

        Section exists in current config (by type and name)?
         - No -> Add section, apply changes, and stop.
         - Yes -> Continue.
        Section is identical to the one in the current config (by option
        values)?
         - No -> Revert current section, mark any affected dependents,
                 add new section, apply changes, and stop.
         - Yes -> Continue.
        Section has not changed but one of its dependencies has?
         - No -> Stop.
         - Yes -> Revert current section, mark any affected dependents,
                  add new section, apply changes, and stop.
        """
        # Map (type, name) -> config
        allConfigs = dict(self.currentConfig)

        # Manage sets of configuration sections.
        # newConfigs: completely new or new versions of existing sections.
        # affectedConfigs: sections that are affected due to dependency
        # changing.
        # undoConfigs: old sections that need to be undone before proceeding.
        newConfigs = set()
        affectedConfigs = set()
        undoConfigs = set()

        # Final list of commands to execute.
        commands = list()

        files = findConfigFiles(search)

        # We will remove things from this set as we find them in the new
        # configuration files.  Anything that remains at the end must have been
        # deleted from its source file.
        deletionSet = self.changingSet(files)

        for config in self.readConfig(files):
            # Check if the section already exists in identical form
            # in our current configuration.
            matchByContent = self.findMatchingConfig(config, byName=False)
            matchByName = self.findMatchingConfig(config, byName=True)

            # If we found anything that matches, then the existing config
            # section should not be deleted.
            if matchByContent in deletionSet:
                deletionSet.remove(matchByContent)
            if matchByName in deletionSet:
                deletionSet.remove(matchByName)

            # If an existing section is identical (in content), we have
            # no new work to do for this section.
            if matchByContent is None:
                if matchByName is not None:
                    # Old section will need to be undone appropriately.
                    undoConfigs.add(matchByName)

                    # Keep track of sections that may be affected by this
                    # one's change.
                    affectedConfigs.update(matchByName.dependents)

                # If it did not exist or is different, add it to our queue
                # of sections to execute.
                newConfigs.add(config)
                allConfigs[config.getTypeAndName()] = config

        # Items from the deletion set should be deleted from memory as well as
        # have their changes undone.
        for config in deletionSet:
            del allConfigs[config.getTypeAndName()]
            undoConfigs.add(config)

        # Generate list of commands to implement configuration.
        for config in affectedConfigs:
            commands.extend(config.undoCommands(self.currentConfig))
        for config in undoConfigs:
            commands.extend(config.undoCommands(self.currentConfig))
        for config in newConfigs:
            commands.extend(config.commands(allConfigs))
        for config in affectedConfigs:
            commands.extend(config.commands(allConfigs))

        # Finally, execute the commands.
        if execute:
            self.execute(commands)

        self.previousCommands = commands
        self.currentConfig = allConfigs

        # Wake up anything that was waiting for the first load to complete.
        self.systemUp.set()

        return self.statusString()

    def readConfig(self, files):
        """
        Load configuration files and return configuration objects.

        This method only loads the configuration files without making any
        changes to the system and returns configuration objects as a generator.
        """
        # Keep track of headers (section type and name) that have been
        # processed so far.  The dictionary maps them to filename, so that we
        # can print a useful warning message about duplicates.
        usedHeaders = dict()

        for fn in files:
            out.info("Reading file {}\n".format(fn))

            uci = UCIConfig(fn)
            config = uci.readConfig()

            for section, options in config:
                # Sections differ in where they put the name, if they have one.
                if "name" in section:
                    name = section['name']
                elif "name" in options:
                    name = options['name']
                else:
                    name = None

                # Get section comment string (optional, but Paradop uses it).
                comment = section.get('comment', None)

                try:
                    cls = configTypeMap[section['type']]
                except:
                    out.warn("Unsupported section type {} in {}\n".format(
                        section['type'], fn))
                    continue

                try:
                    obj = cls.build(self, fn, name, options, comment)
                except:
                    out.warn("Error building object from section {}:{} in "
                             "{}\n".format(section['type'], name, fn))
                    continue

                key = obj.getTypeAndName()
                if key in usedHeaders:
                    out.warn("Section {}:{} from {} overrides section in "
                             "{}\n".format(section['type'], name, fn,
                                           usedHeaders[key]))
                usedHeaders[key] = fn

                yield obj

    def statusString(self):
        """
        Return a JSON string representing status of the system.
        
        The format will be a list of dictionaries.  Each dictionary
        corresponds to a configuration block and contains at the following
        fields.

        type: interface, wifi-device, etc.
        name: name of the section (may be autogenerated for some configs)
        comment: comment from the configuration file or None
        success: True if all setup commands succeeded
        """
        status = list()
        for key, config in self.currentConfig.iteritems():
            success = all(cmd.success() for cmd in config.executed)
            configStatus = {
                'type': config.typename,
                'name': config.name,
                'comment': config.comment,
                'success': success
            }
            status.append(configStatus)
        return json.dumps(status)

    def unload(self, execute=True):
        commands = list()

        for config in self.currentConfig.values():
            commands.extend(config.undoCommands(self.currentConfig))

        # Finally, execute the commands.
        if execute:
            self.execute(commands)

        self.previousCommands = commands
        self.currentConfig = dict()
        return True

    def waitSystemUp(self):
        """
        Wait for the first load to complete and return system status string.
        """
        self.systemUp.wait()
        return self.statusString()
