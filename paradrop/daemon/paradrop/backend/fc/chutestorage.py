###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import sys
import json
import copy
import base64

from pdtools.lib.output import out
from pdtools.lib import pdutils
from paradrop.lib.utils import pdos
from paradrop.lib import settings

from paradrop.lib.utils.storage import PDStorage

from paradrop.lib.chute import Chute


class ChuteStorage(PDStorage):

    """
        ChuteStorage class.

        This class holds onto the list of Chutes on this AP.

        It implements the PDStorage class which allows us to save the chuteList to disk transparently
    """
    # Class variable of chute list so all instances see the same thing
    chuteList = dict()

    def __init__(self, filename=None, reactor=None):
        if(not filename):
            filename = settings.FC_CHUTESTORAGE_SAVE_PATH
        PDStorage.__init__(self, filename, reactor, settings.FC_CHUTESTORAGE_SAVE_TIMER)

        # Has it been loaded?
        if(len(ChuteStorage.chuteList) == 0):
            out.verbose('Loading chutes from disk: %s\n' % (filename))
            self.loadFromDisk()

    def setAttr(self, attr):
        """Save our attr however we want (as class variable for all to see)"""
        ChuteStorage.chuteList = attr

    def getAttr(self):
        """Get our attr (as class variable for all to see)"""
        return ChuteStorage.chuteList

    def getChuteList(self):
        """Return a list of the names of the chutes we know of."""
        return ChuteStorage.chuteList.values()

    def getChute(self, name):
        """Returns a reference to a chute we have in our cache, or None."""
        return ChuteStorage.chuteList.get(name, None)

    def deleteChute(self, ch):
        """Deletes a chute from the chute storage. Can be sent the chute object, or the chute name."""
        if (isinstance(ch, Chute)):
            del ChuteStorage.chuteList[ch.name]
        else:
            del ChuteStorage.chuteList[ch]
        self.saveToDisk()

    def saveChute(self, ch):
        """
            Saves the chute provided in our internal chuteList.
            Also since we just received a new chute to hold onto we should save our ChuteList to disk.
        """
        # check if there is a version of the chute already
        oldch = ChuteStorage.chuteList.get(ch.name, None)
        if(oldch != None):
            newch = copy.deepcopy(oldch)
            # we should merge these chutes so we don't lose any data
            oldch.__dict__.update(ch.__dict__)
            # TODO: do we need to deal with cache separate? Old code we did
        else:
            ChuteStorage.chuteList[ch.name] = ch

        self.saveToDisk()

    def clearChuteStorage(self):
        ChuteStorage.chuteList = {}
        pdos.remove(settings.FC_CHUTESTORAGE_SAVE_PATH)

    #
    # Functions we override to implement PDStorage Properly
    #
    def attrSaveable(self):
        """Returns True if we should save the ChuteList, otherwise False."""
        return (type(ChuteStorage.chuteList) == dict)


if(__name__ == '__main__'): # pragma: no cover
    def usage():
        print('Usage: $0 -ls : print chute storage details')
        exit(0)

    try:
        if(sys.argv[1] != '-ls'):
            usage()
    except Exception as e:
        print(e)
        usage()

    cs = ChuteStorage()

    chutes = cs.getChuteList()
    for ch in chutes:
        print(ch)
