from paradrop.core.chute.chute_storage import ChuteStorage


def saveChute(update):
    chuteStore = ChuteStorage()
    if update.updateType == "delete":
        chuteStore.deleteChute(update.old)
    else:
        # Before saving the chute, store all of the cache values from the
        # installation process because certain functions that read the chute
        # list depend on the cache being there.
        update.new.updateCache(update.cache)

        chuteStore.saveChute(update.new)


def revertChute(update):
    chuteStore = ChuteStorage()
    if update.updateType == "delete":
        chuteStore.saveChute(update.old)
    elif update.old is not None:
        chuteStore.saveChute(update.old)
    else:
        chuteStore.deleteChute(update.new)


def removeAllChutes(update):
    chuteStore = ChuteStorage()
    chuteStore.clearChuteStorage()
