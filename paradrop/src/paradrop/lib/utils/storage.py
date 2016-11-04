###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import pickle

from pdtools.lib.output import out
from pdtools.lib import pdutils
from paradrop.lib.utils import pdos

from twisted.internet.task import LoopingCall


class PDStorage(object):

    """
        ParaDropStorage class.

        This class is designed to be implemented by other classes.
        Its purpose is to make whatever data is considered important persistant to disk.

        This is done by providing a reactor so a "LoopingCall" can be utilized to save to disk.

        The implementer can override functions in order to implement this class:
            getAttr() : Get the attr we need to save to disk
            setAttr() : Set the attr we got from disk
            importAttr(): Takes a payload and returns the properly formatted data
            exportAttr(): Takes the data and returns a payload
            attrSaveable(): Returns True if we should save this attr
    """

    def __init__(self, filename, reactor, saveTimer):
        self.filename = filename
        self.reactor = reactor
        self.saveTimer = saveTimer

        # Setup looping call to keep chute list perisistant only if reactor present
        if(self.reactor):
            self.repeater = self.reactor.LoopingCall(self.saveToDisk)
            self.repeater.start(self.saveTimer)

    def loadFromDisk(self):
        """Attempts to load the data from disk.
            Returns True if success, False otherwise."""

        if(pdos.exists(self.filename)):
            deleteFile = False
            out.info('Loading from disk\n')
            data = ""
            try:
                pyld = pickle.load(pdos.open(self.filename, 'rb'))
                self.setAttr(self.importAttr(pyld))
                return True
            except Exception as e:
                out.err('Error loading from disk: %s\n' % (str(e)))
                deleteFile = True

            # Delete the file
            if(deleteFile):
                try:
                    pdos.unlink(self.filename)
                except Exception as e:
                    out.err('Error unlinking %s\n' % (self.filename))

        return False

    def saveToDisk(self):
        """Saves the data to disk."""
        out.info('Saving to disk (%s)\n' % (self.filename))

        # Make sure they want to save
        if(not self.attrSaveable()):
            return

        # Get whatever the data is
        pyld = self.exportAttr(self.getAttr())

        # Write the file to disk, truncate if it exists
        try:
            pickle.dump(pyld, pdos.open(self.filename, 'wb'))
            pdos.syncFS()

        except Exception as e:
            out.err('Error writing to disk %s\n' % (str(e)))

    def attrSaveable(self):
        """THIS SHOULD BE OVERRIDEN BY THE IMPLEMENTER."""
        return False

    def importAttr(self, pyld):
        """By default do nothing, but expect that this function could be overwritten"""
        return pyld

    def exportAttr(self, data):
        """By default do nothing, but expect that this function could be overwritten"""
        return data
