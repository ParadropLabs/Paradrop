from paradrop.lib.chute import chutestorage


def saveChute(update):
    chuteStore = chutestorage.ChuteStorage()
    if update.updateType == "delete":
        chuteStore.deleteChute(update.old)
    else:
        chuteStore.saveChute(update.new)


def revertChute(update):
    chuteStore = chutestorage.ChuteStorage()
    if update.updateType == "delete":
        chuteStore.saveChute(update.old)
    elif update.old is not None:
        chuteStore.saveChute(update.old)
    else:
        chuteStore.deleteChute(update.new)


def removeAllChutes(update):
    chuteStore = chutestorage.ChuteStorage()
    chuteStore.clearChuteStorage()
