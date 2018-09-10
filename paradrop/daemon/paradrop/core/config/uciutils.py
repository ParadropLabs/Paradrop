from paradrop.lib.utils import uci


def setConfig(update, cacheKeys, filepath):
    """
    Helper function used to modify config file of each various setting in /etc/config/
    Returns:
        True: if it modified a file
        False: if it did NOT cause any modifications
    Raises exception if an error occurs.
    """
    # First pull out all the cache keys from the @new chute
    newconfigs = []

    # chute may be None if a chute installation failed and we are backing out.
    # In that case, newconfigs should be an empty list, meaning there should be
    # nothing left of the chute in the configuration file after we are done.
    if update.new is not None:
        for c in cacheKeys:
            t = update.cache_get(c)
            if t is not None:
                newconfigs.extend(t)

    # Get the chute name. At least one of chute or old should be valid.
    chute_name = update.new.name if update.new is not None else update.old.name

    # Add comment to each config so we can differentiate between different
    # chute specific configs.
    for c, o in newconfigs:
        c['comment'] = chute_name

    # Get the old configs from the file for this chute.
    cfgFile = uci.UCIConfig(filepath)

    # Get all the configs that existed in the old version. Note we are getting
    # the old configs from the etc/config/ file instead of the chute object.
    # This is to improve reliability  - sometimes the file isn't changed it
    # should be because we have reset the board, messed with chutes, etc. and
    # the new/old chuteobjects are identical.
    oldconfigs = cfgFile.getChuteConfigs(chute_name)

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
        cfgFile.save(backupToken="paradrop", internalid=chute_name)
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
