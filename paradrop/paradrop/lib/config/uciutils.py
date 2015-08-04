import traceback

from paradrop.lib.utils import uci
from pdtools.lib.output import out


def appendListItem(options, name, value):
    """
    Add a list item to UCI options.

    The way we store lists for UCI options is rather bizarre, so this function
    takes care of that.

    options: dictionary of options for a UCI section
    name: string name of the list option
    value: string value to append
    """
    if 'list' not in options:
        options['list'] = dict()
    if name not in options['list']:
        options['list'][name] = list()
    options['list'][name].append(value)


def setList(options, name, values):
    """
    Set a list item in UCI options.

    The way we store lists for UCI options is rather bizarre, so this function
    takes care of that.

    options: dictionary of options for a UCI section
    name: string name of the list option
    values: list of string values
    """
    if 'list' not in options:
        options['list'] = dict()
    options['list'][name] = values


def setConfig(chute, old, cacheKeys, filepath):
    """
        Helper function used to modify config file of each various setting in /etc/config/
        Returns:
            True: if it modified a file
            False: if it did NOT cause any modifications
    """
    try:
        # First pull out all the cache keys from the @new chute
        newconfigs = []
        for c in cacheKeys:
            t = chute.getCache(c)
            if(t):
                newconfigs += t

        if(len(newconfigs) == 0):
            out.info('no settings to add %r\n' % (chute))
            # We are no longer returning because we need to remove the old configs if necessary
            # return False

        # add comment to each config so we can differentiate between different chute specific configs
        for e in newconfigs:
            c, o = e
            c['comment'] = chute.name

        # Get the old configs from the file for this chuteid

        # Find the config file
        cfgFile = uci.UCIConfig(filepath)

        # Get all the configs that existed in the old version
        # Note we are getting the old configs from the etc/config/ file instead of the chute object
        # This is to improve reliability  - sometimes the file isn't changed it should be
        # because we have reset the board, messed with chutes, etc. and the new/old chuteobjects are identical
        oldconfigs = cfgFile.getChuteConfigs(chute.name)
        out.info('oldconfigs: %s\n' % (oldconfigs))
        out.info('newconfigs: %s\n' % (newconfigs))

        if (uci.chuteConfigsMatch(oldconfigs, newconfigs)):
            out.info('configs match skipping reloading.\n')
            return False
        else:
            # We need to make changes so delete old configs, load new configs
            out.info('configs dont match, changing chutes and reloading.\n')
            cfgFile.delConfigs(oldconfigs)
            cfgFile.addConfigs(newconfigs)
            cfgFile.save(backupToken="paradrop", internalid=chute.name)
            return True
    except Exception as e:
        out.err('Error: %s\n%s\n' % (str(e), traceback.format_exc()))


def removeConfigs(chute, cacheKeys, filepath):
    """used to modify config file of each various setting in /etc/config/"""
    try:
        # Find the config file
        cfgFile = uci.UCIConfig(filepath)

        # Get all the configs that existed in the file location
        delconfigs = cfgFile.getChuteConfigs(chute.name)

        for cfg in delconfigs:
            c, o = cfg

            out.warn('CONFIG: %r\nOPTIONS: %r\n' % (c, o))
            cfgFile.delConfig(c, o)

        cfgFile.save(backupToken="paradrop", internalid=chute.name)

    except Exception as e:
        out.err('Error: %s\n%s\n' % (str(e), traceback.format_exc()))


def restoreConfigFile(chute, configname):
    """
    Restore a system config file from backup.

    This can only be used during a chute update operation to revert changes
    that were made during that update operation.

    configname: name of configuration file ("network", "wireless", etc.)
    """
    filepath = uci.getSystemPath(configname)
    cfgFile = uci.UCIConfig(filepath)
    cfgFile.restore(backupToken="paradrop", saveBackup=False)
