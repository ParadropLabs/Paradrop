from . import main


def reloadAll(adapter=''):
    """
    Reload all files from the system configuration directory.

    This function blocks until the request completes.  On completion it returns
    a status string, which is a JSON list of loaded configuration sections with
    a 'success' field.
    For critical errors it will return None.
    """
    return main.configManager.loadConfig()


def reload(path, adapter=''):
    """
    Reload file(s) specified by path.

    This function blocks until the request completes.  On completion it returns
    a status string, which is a JSON list of loaded configuration sections with
    a 'success' field.
    For critical errors it will return None.
    """
    return main.configManager.loadConfig(path)


def waitSystemUp(adapter=''):
    """
    Wait for the configuration daemon to finish its first load.

    This function blocks until the request completes.  On completion it returns
    a status string, which is a JSON list of loaded configuration sections with
    a 'success' field.
    For critical errors it will return None.
    """
    return main.configManager.waitSystemUp()
