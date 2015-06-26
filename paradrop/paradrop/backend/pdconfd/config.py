import os
import subprocess
from pprint import pprint

from paradrop.internal.utils.uci import OpenWrtConfig

CONFIG_DIR = "/etc/config"

class ConfigObject(object):
    typename = None
    required = []

    def missingOptions(self, data):
        missing = [x for x in self.required if x not in data]
        return missing

class ConfigInterface(ConfigObject):
    typename = "interface"
    required = ["proto", "ifname"]

    def commands(self):
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

    @classmethod
    def build(cls, options):
        interface = cls()
        interface.proto = options['proto']
        interface.ifname = options['ifname']
        if interface.proto == "static":
            interface.required.extend(["ipaddr", "netmask"])
            interface.ipaddr = options['ipaddr']
            interface.netmask = options['netmask']
        interface.enabled = True
        if "enabled" in options:
            interface.enabled = (options['enabled'] != '0')
        return interface

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

def loadConfig(search=None):
    files = findConfigFiles(search)

    commands = list()

    for fn in files:
        print("Trying file {}".format(fn))
        uci = OpenWrtConfig(fn)
        config = uci.readConfig()

        for section, options in config:
            if section['type'] == "interface":
                interface = ConfigInterface.build(options)
                commands.extend(interface.commands())

    for cmd in commands:
        print("Command: {}".format(" ".join(cmd)))
        result = subprocess.call(cmd)
        print("Result: {}".format(result))

    return True

if __name__=="__main__":
    loadConfig()

