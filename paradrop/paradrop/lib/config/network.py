
from paradrop.lib.utils.output import out, logPrefix


def getNetworkConfig(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # old code under lib.internal.chs.chutelxc same function name

    # Fill in the gaps of knowledge between what the dev provided us in their config
    # and what would be required to add all the config changes to get the chute working
    # By the end of this function there should be a cache:networkInterfaces key containing
    # a list of dictionary objects for each interface we will need to create, including netmasks
    # IP addresses, etc.. this is important to allow all other modules to know what the IP addr is
    # for this chute, etc..

def getOSNetworkConfig(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # old code under lib.internal.chs.chutelxc same function name
    # Take the cache:networkInterfaces key and generate the UCI specific OS config we need
    # to inact the chute changes, should create a cache:osNetworkConfig key

def setOSNetworkConfig(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # old code under lib.internal.chs.chutelxc same function name
    # Takes the config generated (cache:osNetworkConfig) and uses the UCI module to actually push
    # it to the disk

def getVirtNetworkConfig(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    # old code under lib.internal.chs.chutelxc same function name
    # Takes any network specific config and sets up the cache:virtNetworkConfig
    # this would be the place to put anything into HostConfig or the dockerfile we need
