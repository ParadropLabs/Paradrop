from paradrop.lib.utils import uci
from paradrop.base.output import out


def setConfig(chute, old, cacheKeys, filepath):
    """
    Helper function used to modify config file of each various setting in /etc/config/
    Returns:
        True: if it modified a file
        False: if it did NOT cause any modifications
    Raises exception if an error occurs.
    """
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

    if (uci.chuteConfigsMatch(oldconfigs, newconfigs)):
        # configs match, skipping reloading
        # Save a backup in case we need to restore.
        cfgFile.backup(backupToken="paradrop")
        return False
    else:
        # We need to make changes so delete old configs, load new configs
        # configs don't match, changing chutes and reloading
        cfgFile.delConfigs(oldconfigs)
        cfgFile.addConfigs(newconfigs)
        cfgFile.save(backupToken="paradrop", internalid=chute.name)
        return True


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
