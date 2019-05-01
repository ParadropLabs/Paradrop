import heapq
import json
import os
import threading

import six

from paradrop.base.output import out
from paradrop.lib.utils import pdosq
from paradrop.lib.utils.uci import UCIConfig, getSystemConfigDir

# Import all of the modules defining section types, so that all subclasses of
# ConfigObject are known. These are imported only for their side effects.
from . import dhcp
from . import firewall
from . import network
from . import parprouted
from . import qos
from . import wireless

from .base import ConfigObject
from .command import CommandList, ErrorCommand


# Silence pyflakes warning about unused imports.
assert dhcp
assert firewall
assert network
assert parprouted
assert qos
assert wireless


# Map of type names to the classes that handle them.  We now prefer the
# extended type name, e.g. "network:interface", because there can be
# conflicting types, e.g. "qos:interface".
configTypeMap = dict()
for cls in ConfigObject.__subclasses__():
    extended = "{}:{}".format(cls.getModule(), cls.typename)
    configTypeMap[extended] = cls

    existing = configTypeMap.get(cls.typename, None)
    if existing is None or existing.maskable:
        configTypeMap[cls.typename] = cls


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
        search = getSystemConfigDir()

    files = list()
    if os.path.isfile(search):
        files.append(search)
    elif os.path.isdir(search):
        for fn in os.listdir(search):
            path = os.path.join(search, fn)
            files.append(path)
    else:
        path = os.path.join(getSystemConfigDir(), search)
        if os.path.isfile(path):
            files.append(path)

    return files


class ConfigManager(object):

    def __init__(self, writeDir, execCommands=True):
        """
        writeDir: directory to use for generated config files (e.g. hostapd.conf).
        execCommands: whether or not to run commands (set to False for testing).
        """
        self.writeDir = writeDir
        self.execCommands = execCommands

        # Make sure directory exists.
        pdosq.makedirs(writeDir)

        self.previousCommands = list()
        self.currentConfig = dict()
        self.nextSectionId = 0

        # Number of objects requiring IP forwarding.
        # If >0, we need to enable system-wide.
        # If ==0, we can probably disable.
        self.forwardingCount = 0

        # Track whether we have loaded the conntrack kernel module.  We need to
        # make sure the module is loaded before adding iptables rules related
        # to connection state.
        self.conntrackLoaded = False

        # Allow threads to wait for first load to complete.  This will be set
        # after the first load completes and will remain set thereafter.
        self.systemUp = threading.Event()

        # Track epoch number so that we know which configuration sections
        # were applied in the most recent epoch.
        self.epoch = 0

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
        return self.previousCommands

    def execute(self, commands):
        """
        Execute commands.

        Takes a CommandList object.
        """
        for cmd in commands.commands():
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
        self.epoch += 1

        # Map (type, name) -> config
        allConfigs = dict(self.currentConfig)

        # Manage sets of configuration sections.
        # newConfigs: completely new or new versions of existing sections.
        # affectedConfigs: sections that are affected due to dependency
        # changing.
        # undoConfigs: old sections that need to be undone before proceeding.
        newConfigs = set()
        updatedConfigs = set()
        undoConfigs = set()

        # Final list of commands to execute.
        commands = CommandList()

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
            if matchByContent is not None:
                # Just make sure the new config's internalName matches the old
                # config's.  This is mainly for anonymous sections because they
                # have auto-generated unique names.
                config.internalName = matchByContent.internalName

            else:
                if matchByName is not None:
                    # Old section will need to be updated appropriately.
                    updatedConfigs.add(matchByName)

                    # Keep track of sections that may be affected by this
                    # one's change.
                    updatedConfigs.update(matchByName.dependents)

                    # Remove links to the old version because it will be
                    # redundant after the new configuration goes into effect.
                    matchByName.removeFromParents()

                else:
                    # If it did not exist or is different, add it to our queue
                    # of sections to execute.
                    newConfigs.add(config)

                # Mark that the config section was applied in this epoch.
                config.epoch = self.epoch

                allConfigs[config.getTypeAndName()] = config

        # Items from the deletion set should be deleted from memory as well as
        # have their changes undone.
        for config in deletionSet:
            del allConfigs[config.getTypeAndName()]
            config.removeFromParents()
            undoConfigs.add(config)

        # Remove configs that are in both sets---we should not try to reload
        # updated configs that are supposed to be removed.
        updatedConfigs -= undoConfigs

        undoWork = ConfigObject.prioritizeConfigs(updatedConfigs | undoConfigs,
                reverse=True)
        heapq.heapify(undoWork)

        while undoWork:
            prio, config = heapq.heappop(undoWork)

            try:
                if config in undoConfigs:
                    commands.extend(config.revert(allConfigs))
                else:
                    new = allConfigs[config.getTypeAndName()]
                    commands.extend(config.updateRevert(new, allConfigs))
            except Exception as error:
                commands.append(prio, ErrorCommand(error, config))

        applyWork = ConfigObject.prioritizeConfigs(updatedConfigs | newConfigs)
        heapq.heapify(applyWork)

        while applyWork:
            prio, config = heapq.heappop(applyWork)

            try:
                if config in newConfigs:
                    commands.extend(config.apply(allConfigs))
                else:
                    new = allConfigs[config.getTypeAndName()]
                    commands.extend(config.updateApply(new, allConfigs))
            except Exception as error:
                commands.append(prio, ErrorCommand(error, config))

            # Reset list of executed commands so that previous failures do not
            # haunt us.
            config.executed = list()

        # Finally, execute the commands.
        if execute and self.execCommands:
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

            # Extract just the filename (e.g. wireless, network, qos).
            basename = os.path.basename(fn)

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

                # Try looking up by extended type first.  It turns out, both
                # "network" and "qos" configuration files should support
                # sections with typename "interface".  We can disambiguate
                # them by calling the latter one "qos:interface".
                ext_type = "{}:{}".format(basename, section['type'])
                if ext_type in configTypeMap:
                    cls = configTypeMap[ext_type]
                elif section['type'] in configTypeMap:
                    cls = configTypeMap[section['type']]
                else:
                    out.warn("Unsupported section type {} in {}\n".format(
                        section['type'], fn))
                    continue

                try:
                    obj = cls.build(self, fn, name, options, comment)
                except Exception as e:
                    out.warn("Error building object from section {}:{} in "
                             "{}\n".format(section['type'], name, fn))
                    out.warn(e)
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
        for key, config in six.iteritems(self.currentConfig):
            success = all(cmd.success() for cmd in config.executed)
            configStatus = {
                'type': config.typename,
                'name': config.name,
                'comment': config.comment,
                'success': success,
                'age': self.epoch - config.epoch
            }
            status.append(configStatus)
        return json.dumps(status)

    def unload(self, execute=True):
        commands = CommandList()

        undoWork = ConfigObject.prioritizeConfigs(self.currentConfig.values())
        heapq.heapify(undoWork)

        while undoWork:
            prio, config = heapq.heappop(undoWork)
            commands.extend(config.revert(self.currentConfig))

        # Finally, execute the commands.
        if execute and self.execCommands:
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
