from paradrop.core.chute.chute_storage import ChuteStorage


def saveChute(update):
    """
    Save information about the chute to the filesystem.
    """
    chuteStore = ChuteStorage()
    if update.updateType == "delete":
        chuteStore.deleteChute(update.old)
    else:
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
