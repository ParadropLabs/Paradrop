from paradrop.backend.pdconfd.config.command import Command
from paradrop.backend.pdconfd.config.manager import ConfigManager

CONFIG_FILE = "/tmp/test-config"
WRITE_DIR = "/tmp"

ETH0_CONFIG = """
config interface eth0
    option ifname 'eth0'
    option proto 'static'
    option ipaddr '129.168.33.66'
    option netmask '255.255.255.0'
"""


def write_file(path, data):
    with open(path, "w") as output:
        output.write(data)


def test_command():
    """
    Test command execution

    The true and false commands should reliably succeed and fail in most Linux
    environments.
    """
    cmd = ["true"]
    command = Command(0, cmd)
    command.execute()
    assert command.success()

    cmd = ["false"]
    command = Command(0, cmd)
    command.execute()
    assert not command.success()


def test_load_interface():
    """
    Test loading a configuration file that specifies an interface
    """
    write_file(CONFIG_FILE, ETH0_CONFIG)
    manager = ConfigManager(WRITE_DIR)
    manager.loadConfig(search=CONFIG_FILE, execute=False)
    commands = manager.previousCommands
    assert len(commands) > 0
