import os
import shutil
import tempfile

from mock import patch


CONFIG_DIR = "tests/paradrop/confd/config.d"

@patch("paradrop.confd.manager.getSystemConfigDir")
@patch("paradrop.confd.manager.os.path.isfile")
@patch("paradrop.confd.manager.os.path.isdir")
@patch("paradrop.confd.manager.os.listdir")
def test_findConfigFiles(listdir, isdir, isfile, getSystemConfigDir):
    """
    Test the findConfigFiles function
    """
    from paradrop.confd.manager import findConfigFiles

    isfile.return_value = True
    result = findConfigFiles(search="foo")
    for fn in result:
        print(fn)
    assert result == ["foo"]

    print("---")
    isfile.return_value = False
    isdir.return_value = True
    listdir.return_value = ["foo", "bar"]
    result = findConfigFiles(search="dir")
    for fn in result:
        print(fn)
    assert result == ["dir/foo", "dir/bar"]

    print("---")
    getSystemConfigDir.return_value = "/etc/config"
    isfile.side_effect = [False, True]
    isdir.return_value = False
    result = findConfigFiles(search="foo")
    for fn in result:
        print(fn)
    assert result == ["/etc/config/foo"]

    print("---")
    getSystemConfigDir.return_value = "/etc/config"
    isfile.side_effect = None
    isfile.return_value = False
    isdir.return_value = True
    listdir.return_value = ["foo"]
    result = findConfigFiles()
    for fn in result:
        print(fn)
    assert result == ["/etc/config/foo"]


def test_bad_config():
    """
    Test how pdconf manager handles a bad configuration section
    """
    from paradrop.confd.manager import ConfigManager

    manager = ConfigManager(writeDir="/tmp")

    source = os.path.join(CONFIG_DIR, "bad_config")
    manager.loadConfig(search=source, execute=False)


def test_change_channel():
    """
    Test how pdconf manager handles changing a WiFi card's channel
    """
    from paradrop.confd.manager import ConfigManager

    # We want to use the same path for the config file at every step of the
    # test case, as this allows the manager to detect when a section is
    # removed.
    temp = tempfile.mkdtemp()
    confFile = os.path.join(temp, "config")

    manager = ConfigManager(writeDir="/tmp")

    source = os.path.join(CONFIG_DIR, "change_channel_1")
    shutil.copyfile(source, confFile)
    manager.loadConfig(search=confFile, execute=False)

    for cmd in manager.previousCommands:
        print(cmd)

    source = os.path.join(CONFIG_DIR, "change_channel_2")
    shutil.copyfile(source, confFile)
    manager.loadConfig(search=confFile, execute=False)

    print("---")
    for cmd in manager.previousCommands:
        print(cmd)

    # Changing the channel should restart hostapd but not delete and recreate
    # the wireless interface.
    assert "del" not in manager.previousCommands

    source = os.path.join(CONFIG_DIR, "change_channel_3")
    shutil.copyfile(source, confFile)
    manager.loadConfig(search=confFile, execute=False)

    print("---")
    for cmd in manager.previousCommands:
        print(cmd)

    # The third config should bring down hostapd, not start it.
    assert "kill" in manager.previousCommands
    assert "bin/hostapd" not in manager.previousCommands

    # Cleanup
    shutil.rmtree(temp)


@patch("paradrop.confd.command.Command.execute")
def test_manager_execute(execute):
    """
    Test the manager execute method
    """
    from paradrop.confd.manager import ConfigManager

    manager = ConfigManager(writeDir="/tmp")

    source = os.path.join(CONFIG_DIR, "multi_ap")
    manager.loadConfig(search=source, execute=True)
    assert execute.call_count > 1

    # Verify the order of commands:
    # "interface add" < "addr add" < "hostapd"
    ifaceAdd = None
    addrAdd = None
    hostapd = None
    i = 0
    for cmd in manager.previousCommands.commands():
        print(cmd)
        if "interface add" in cmd:
            ifaceAdd = i
        elif "addr add" in cmd:
            addrAdd = i
        elif "hostapd" in cmd:
            hostapd = i
        i += 1
    assert ifaceAdd < addrAdd and addrAdd < hostapd

    execute.reset_mock()
    manager.unload(execute=True)
    assert execute.call_count > 1

    # Verify the order of commands:
    # "kill" < "addr del" < "iw dev ... del"
    print("---")
    kill = None
    addrDel = None
    iwDev = None
    i = 0
    for cmd in manager.previousCommands.commands():
        print(cmd)
        if "kill" in cmd:
            kill = i
        elif "addr del" in cmd:
            addrDel = i
        elif "iw dev" in cmd:
            iwDev = i
        i += 1
    assert kill < addrDel and addrDel < iwDev
