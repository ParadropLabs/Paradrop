import os
import tempfile


CONFIG_DIR = "tests/paradrop/backend/pdconfd/config/config.d"


def test_change_channel():
    """
    Test how pdconf manager handles changing a WiFi card's channel
    """
    from paradrop.backend.pdconfd.config.manager import ConfigManager

    manager = ConfigManager(writeDir="/tmp")

    config1Path = os.path.join(CONFIG_DIR, "change_channel_1")
    manager.loadConfig(search=config1Path, execute=False)
    
    for cmd in manager.previousCommands:
        print(cmd.command)

    config2Path = os.path.join(CONFIG_DIR, "change_channel_2")
    manager.loadConfig(search=config2Path, execute=False)

    print("---")
    for cmd in manager.previousCommands:
        print(cmd.command)

    config3Path = os.path.join(CONFIG_DIR, "change_channel_3")
    manager.loadConfig(search=config3Path, execute=False)

    print("---")
    for cmd in manager.previousCommands:
        print(cmd.command)

    # The third config should bring down hostapd.
    assert all("hostapd" not in cmd for cmd in manager.previousCommands)
