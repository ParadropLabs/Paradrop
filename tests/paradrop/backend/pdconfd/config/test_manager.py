import os
import shutil
import tempfile


CONFIG_DIR = "tests/paradrop/backend/pdconfd/config/config.d"


def test_change_channel():
    """
    Test how pdconf manager handles changing a WiFi card's channel
    """
    from paradrop.backend.pdconfd.config.manager import ConfigManager

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

    # TODO: Add this when update works---we should not need to delete and
    # re-add the virtual wireless interface.
#    assert all("del" not in cmd for cmd in manager.previousCommands)

    source = os.path.join(CONFIG_DIR, "change_channel_3")
    shutil.copyfile(source, confFile)
    manager.loadConfig(search=confFile, execute=False)

    print("---")
    for cmd in manager.previousCommands:
        print(cmd)

    # The third config should bring down hostapd, not start it.
    assert all("hostapd" not in cmd for cmd in manager.previousCommands)
