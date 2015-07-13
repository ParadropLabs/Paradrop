import ipaddress
import os
import string
import subprocess
from pprint import pprint

from paradrop.lib.utils.output import logPrefix, out
from paradrop.lib.utils.uci import UCIConfig

CONFIG_DIR = "/etc/config"

WRITE_DIR = "/var/run"
""" Directory for daemon configuration files, PID files, etc. """

def isHexString(data):
    """
    Test if a string contains only hex digits.
    """
    return all(c in string.hexdigits for c in data)

class ConfigObject(object):
    nextId = 0
    typename = None
    options = []

    def __init__(self):
        self.id = ConfigObject.nextId
        ConfigObject.nextId += 1

        self.source = None
        self.name = "s{:08x}".format(self.id)
        self.dependents = set()

    def __hash__(self):
        return hash(self.getTypeAndName())

    def __repr__(self):
        return "{}({}:{}:{})".format(self.__class__.__name__,
                self.source, self.typename, self.name)

    def __str__(self):
        return "{}:{}".format(self.typename, self.name)

    def addDependent(self, dep):
        self.dependents.add(dep)

    def commands(self, allConfigs):
        return []

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
        return []

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
    def build(cls, manager, source, name, options):
        """
        Build a config object instance from the UCI section.

        Arguments:
        source -- file containing this configuration section
        name -- name of the configuration section
                If None, a unique name will be generated. 
        options -- dictionary of options loaded from the section
        """
        obj = cls()
        obj.manager = manager
        obj.source = source

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

        return obj

class ConfigDhcp(ConfigObject):
    typename = "dhcp"

    options = [
        {"name": "interface", "type": str, "required": True, "default": None},
        {"name": "leasetime", "type": str, "required": True, "default": "12h"},
        {"name": "limit", "type": int, "required": True, "default": 150},
        {"name": "start", "type": int, "required": True, "default": 100}
    ]

    def commands(self, allConfigs):
        # Look up the interface - may fail.
        interface = self.lookup(allConfigs, "interface", self.interface)

        network = ipaddress.IPv4Network(u"{}/{}".format(
            interface.ipaddr, interface.netmask), strict=False)

        # TODO: Error checking!
        firstAddress = network.network_address + self.start
        lastAddress = firstAddress + self.limit

        leaseFile = "/tmp/dnsmasq-{}.leases".format(self.interface)
        pidFile = "/tmp/dnsmasq-{}.pid".format(self.interface)

        if False:
            # TODO: Figure out how to write a configuration file and have the
            # target daemon be able to load that file.  In principle this code
            # should work, but something about how Snappy handles filesystem or
            # process isolation breaks it.  We write the file
            # /etc/dnsmasq-foo.conf, it appears in the filesystem, but then
            # dnsmasq says it cannot find it.  Luckily, dnsmasq can be
            # configured either by command line arguments or by configuration
            # file.  Other daemons (e.g.  hostapd) are not so flexible, so we
            # need to solve this.
            outputPath = "/tmp/dnsmasq-{}.conf".format(self.interface)
            with open(outputPath, "w") as outputFile:
                outputFile.write("#" * 80 + "\n")
                outputFile.write("# dnsmasq configuration file generated by pdconfd\n")
                outputFile.write("# Source: {}\n".format(self.source))
                outputFile.write("# Section: config {} {}\n".format(
                    ConfigDhcp.typename, self.name))
                outputFile.write("#" * 80 + "\n")
                outputFile.write("interface={}\n".format(interface.ifname))
                outputFile.write("dhcp-range={},{},{}\n".format(
                    str(firstAddress), str(lastAddress), self.leasetime))
                outputFile.write("dhcp-leasefile={}\n".format(leaseFile))
            cmd = ["dnsmasq", "--conf-file={}".format(outputPath),
                    "--pid-file={}".format(pidFile)]
        else:
            cmd = ["/apps/paradrop/current/bin/dnsmasq",
                    "--interface={}".format(interface.ifname),
                    "--dhcp-range={},{},{}".format(str(firstAddress), str(lastAddress), self.leasetime),
                    "--dhcp-leasefile={}".format(leaseFile),
                    "--pid-file={}".format(pidFile)]

        self.pidFile = pidFile
        return [cmd]

    def undoCommands(self, allConfigs):
        try:
            with open(self.pidFile, "r") as inputFile:
                pid = inputFile.read().strip()
            cmd = ["kill", pid]
            return [cmd]
        except:
            # No pid file --- maybe dnsmasq was not running?
            out.warn("** {} File not found: {}\n".format(
                logPrefix(), self.pidFile))
            return []

class ConfigInterface(ConfigObject):
    typename = "interface"

    options = [
        {"name": "proto", "type": str, "required": True, "default": None},
        {"name": "ifname", "type": str, "required": True, "default": None},
        {"name": "enabled", "type": bool, "required": False, "default": True},
        {"name": "ipaddr", "type": str, "required": False, "default": None},
        {"name": "netmask", "type": str, "required": False, "default": None}
    ]

    def commands(self, allConfigs):
        commands = list()
        if self.proto == "static":
            cmd = ["ip", "addr", "flush", "dev", self.ifname]
            commands.append(cmd)

            cmd = ["ip", "addr", "add", 
                    "{}/{}".format(self.ipaddr, self.netmask),
                    "dev", self.ifname]
            commands.append(cmd)

            updown = "up" if self.enabled else "down"
            cmd = ["ip", "link", "set", "dev", self.ifname, updown]
            commands.append(cmd)

        return commands

class ConfigRedirect(ConfigObject):
    typename = "redirect"

    options = [
        {"name": "src", "type": str, "required": False, "default": None},
        {"name": "src_ip", "type": str, "required": False, "default": None},
        {"name": "src_dip", "type": str, "required": False, "default": None},
        {"name": "src_port", "type": str, "required": False, "default": None},
        {"name": "src_dport", "type": str, "required": False, "default": None},
        {"name": "proto", "type": str, "required": True, "default": "tcpudp"},
        {"name": "dest", "type": str, "required": False, "default": None},
        {"name": "dest_ip", "type": str, "required": False, "default": None},
        {"name": "dest_port", "type": str, "required": False, "default": None},
        {"name": "target", "type": str, "required": False, "default": "DNAT"}
    ]

    def __commands_dnat(self, allConfigs, action):
        """
        Generate DNAT iptables rules.
        """
        commands = list()

        src_zone = self.lookup(allConfigs, "zone", self.src)

        # Special cases: 
        # None->skip protocol and port arguments,
        # tcpudp->[tcp, udp]
        if self.proto is None:
            protocols = [None]
        elif self.proto == "tcpudp":
            protocols = ["tcp", "udp"]
        else:
            protocols = [self.proto]

        for interface in src_zone.interfaces(allConfigs):
            for proto in protocols:
                cmd = ["iptables", "--table", "nat",
                        action, "PREROUTING",
                        "--in-interface", interface.ifname]

                if self.src_ip is not None:
                    cmd.extend(["--source", self.src_ip])
                if self.src_dip is not None:
                    cmd.extend(["--destination", self.src_dip])
                if proto is not None:
                    cmd.extend(["--proto", proto])
                    if self.src_port is not None:
                        cmd.extend(["--sport", self.src_port])
                    if self.src_dport is not None:
                        cmd.extend(["--dport", self.src_dport])

                if self.dest_ip is not None:
                    if self.dest_port is not None:
                        cmd.extend(["--jump", "DNAT", "--to-destination",
                            "{}:{}".format(self.dest_ip, self.dest_port)])
                    else:
                        cmd.extend(["--jump", "DNAT", "--to-destination", self.dest_ip])
                elif self.dest_port is not None:
                    cmd.extend(["--jump", "REDIRECT", "--to-port", self.dest_port])

                cmd.extend(["--match", "comment", "--comment",
                    "pdconfd {} {}".format(self.typename, self.name)])

                commands.append(cmd)

        return commands

    def __commands_snat(self, allConfigs, action):
        """
        Generate SNAT iptables rules.
        """
        commands = list()
        # TODO: implement SNAT rules
        return commands

    def commands(self, allConfigs):
        if self.target == "DNAT":
            commands = self.__commands_dnat(allConfigs, "--insert")
        elif self.target == "SNAT":
            commands = self.__commands_snat(allConfigs, "--insert")
        else:
            commands = list()

        self.manager.forwardingCount += 1
        if self.manager.forwardingCount == 1:
            cmd = ["sysctl", "--write",
                    "net.ipv4.conf.all.forwarding=1"]
            commands.append(cmd)
        
        return commands

    def undoCommands(self, allConfigs):
        if self.target == "DNAT":
            commands = self.__commands_dnat(allConfigs, "--delete")
        elif self.target == "SNAT":
            commands = self.__commands_snat(allConfigs, "--delete")
        else:
            commands = list()

        self.manager.forwardingCount -= 1
        if self.manager.forwardingCount == 0:
            cmd = ["sysctl", "--write",
                    "net.ipv4.conf.all.forwarding=0"]
            commands.append(cmd)

        return commands

class ConfigWifiDevice(ConfigObject):
    typename = "wifi-device"

    options = [
        {"name": "type", "type": str, "required": True, "default": None},
        {"name": "channel", "type": int, "required": True, "default": 1}
    ]

    def commands(self, allConfigs):
        commands = list()

        cmd = ["iw", "dev", self.name, "set", "channel", str(self.channel)]
        commands.append(cmd)

        return commands

class ConfigWifiIface(ConfigObject):
    typename = "wifi-iface"

    options = [
        {"name": "device", "type": str, "required": True, "default": None},
        {"name": "mode", "type": str, "required": True, "default": "ap"},
        {"name": "ssid", "type": str, "required": True, "default": "Paradrop"},
        {"name": "network", "type": str, "required": True, "default": "lan"},
        {"name": "encryption", "type": str, "required": False, "default": None},
        {"name": "key", "type": str, "required": False, "default": None}
    ]

    def commands(self, allConfigs):
        commands = list()

        if self.mode != "ap":
            out.warn("** {} Mode {} not supported\n".format(logPrefix(), self.mode))
            raise Exception("WiFi interface mode not supported")

        # Look up the wifi-device section.
        wifiDevice = self.lookup(allConfigs, "wifi-device", self.device)

        # Look up the interface section.
        interface = self.lookup(allConfigs, "interface", self.network)

        outputPath = "{}/hostapd-{}.conf".format(self.manager.writeDir, self.name)
        with open(outputPath, "w") as outputFile:
            # Write our informative header block.
            outputFile.write("#" * 80 + "\n")
            outputFile.write("# hostapd configuration file generated by pdconfd\n")
            outputFile.write("# Source: {}\n".format(self.source))
            outputFile.write("# Section: config {} {}\n".format(
                self.typename, self.name))
            outputFile.write("#" * 80 + "\n")

            # Write essential options.
            outputFile.write("interface={}\n".format(wifiDevice.name))
            outputFile.write("ssid={}\n".format(self.ssid))
            outputFile.write("channel={}\n".format(wifiDevice.channel))

            # Optional encryption options.
            if self.encryption is None or self.encryption == "none":
                pass
            elif self.encryption == "psk2":
                outputFile.write("wpa=1\n")
                # If key is a 64 character hex string, then treat it as the PSK
                # directly, else treat it as a passphrase.
                if len(self.key) == 64 and isHexString(self.key):
                    outputFile.write("wpa_psk={}\n".format(self.key))
                else:
                    outputFile.write("wpa_passphrase={}\n".format(self.key))
            else:
                out.warn("** {} Encryption type {} not supported (supported: none|psk2)".format(
                    logPrefix(), self.encryption))
                raise Exception("Encryption type not supported")

        self.pidFile = "{}/hostapd-{}.pid".format(self.manager.writeDir, self.name)

        cmd = ["hostapd", "-P", self.pidFile, "-B", outputPath]
        commands.append(cmd)

        return commands

    def undoCommands(self, allConfigs):
        try:
            with open(self.pidFile, "r") as inputFile:
                pid = inputFile.read().strip()
            cmd = ["kill", pid]
            return [cmd]
        except:
            # No pid file --- maybe it was not running?
            out.warn("** {} File not found: {}\n".format(
                logPrefix(), self.pidFile))
            return []

class ConfigZone(ConfigObject):
    typename = "zone"

    options = [
        {"name": "name", "type": str, "required": True, "default": None},
        {"name": "network", "type": list, "required": False, "default": None},
        {"name": "masq", "type": bool, "required": False, "default": False},
        {"name": "input", "type": str, "required": False, "default": "DROP"},
        {"name": "forward", "type": str, "required": False, "default": "DROP"},
        {"name": "output", "type": str, "required": False, "default": "DROP"}
    ]

    def interfaces(self, allConfigs):
        """
        List of interfaces in this zone (generator).
        """
        if self.network is not None:
            for networkName in self.network:
                # Look up the interface - may fail.
                interface = self.lookup(allConfigs, "interface", networkName)
                yield interface

    def __commands_iptables(self, allConfigs, action):
        commands = list()

        if self.masq:
            for interface in self.interfaces(allConfigs):
                cmd = ["iptables", "--table", "nat",
                        action, "POSTROUTING",
                        "--out-interface", interface.ifname,
                        "--jump", "MASQUERADE",
                        "--match", "comment", "--comment", 
                        "pdconfd {} {}".format(self.typename, self.name)]
                commands.append(cmd) 

        return commands

    def commands(self, allConfigs):
        commands = self.__commands_iptables(allConfigs, "--insert")

        if self.masq:
            self.manager.forwardingCount += 1
            if self.manager.forwardingCount == 1:
                cmd = ["sysctl", "--write",
                        "net.ipv4.conf.all.forwarding=1"]
                commands.append(cmd)
        
        return commands

    def undoCommands(self, allConfigs):
        commands = self.__commands_iptables(allConfigs, "--delete")

        if self.masq:
            self.manager.forwardingCount -= 1
            if self.manager.forwardingCount == 0:
                cmd = ["sysctl", "--write",
                        "net.ipv4.conf.all.forwarding=0"]
                commands.append(cmd)

        return commands

# Map of type names to the classes that handle them.
configTypeMap = dict()
for cls in ConfigObject.__subclasses__():
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

class ConfigManager(object):
    def __init__(self, writeDir=WRITE_DIR):
        self.writeDir = writeDir

        self.currentConfig = dict()
        self.nextSectionId = 0

        # Number of objects requiring IP forwarding.
        # If >0, we need to enable system-wide.
        # If ==0, we can probably disable.
        self.forwardingCount = 0

    def changingSet(self, files):
        """
        Return the sections from the current configuration that may have changed.

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
        Section is identical to the one in the current config (by option values)?
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
        # affectedConfigs: sections that are affected due to dependency changing.
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
        for cmd in commands:
            print("Command: {}".format(" ".join(cmd)))
            if execute:
                result = subprocess.call(cmd)
                print("Result: {}".format(result))

        self.currentConfig = allConfigs
        return True

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
            out.info("-- {} Reading file {}\n".format(logPrefix(), fn))

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

                try:
                    cls = configTypeMap[section['type']]
                except:
                    out.warn("** {} Unsupported section type {} in {}\n".format(
                        logPrefix(), section['type'], fn))
                    continue

                try:
                    obj = cls.build(self, fn, name, options)
                except:
                    out.warn("** {} Error building object from section {}:{} in {}\n".format(
                        logPrefix(), section['type'], name, fn))
                    continue

                key = obj.getTypeAndName()
                if key in usedHeaders:
                    out.warn("** {} Section {}:{} from {} overrides section in {}\n".format(
                        logPrefix(), section['type'], name, fn, usedHeaders[key]))
                usedHeaders[key] = fn

                yield obj

    def unload(self, execute=True):
        commands = list()

        for config in self.currentConfig.values():
            commands.extend(config.undoCommands(self.currentConfig))

        for cmd in commands:
            print("Command: {}".format(" ".join(cmd)))
            if execute:
                result = subprocess.call(cmd)
                print("Result: {}".format(result))

        self.currentConfig = dict()
        return True

if __name__=="__main__":
    manager = ConfigManager(writeDir="/tmp")
    print("Loading configuration files:")
    manager.loadConfig(execute=False)
    print("\nReloading configuration files:")
    manager.loadConfig(execute=False)
    print("\nUnloading configuration files:")
    manager.unload(execute=False)

