###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import pickle

from paradrop.lib.utils.output import out, logPrefix
from paradrop.lib.utils import pdutils
from paradrop.lib.utils import pdos

from twisted.internet.task import LoopingCall

class PDStorage:
    """
        ParaDropStorage class.

        This class is designed to be implemented by other classes.
        Its purpose is to make whatever data is considered important persistant to disk.
        
        This is done by providing a reactor so a "LoopingCall" can be utilized to save to disk.
        
        @importantAttr is used as the attribute which should be saved.
        
        The implementer is expected to override 3 functions in order to implement this class:
            importAttr(): Takes a payload and returns the properly formatted data
            exportAttr(): Takes the data and returns a payload
            attrSaveable(): Returns True if we should save this attr
    """

    def __init__(self, filename, importantAttr, reactor, saveTimer):
        self.filename = filename
        self.reactor = reactor
        self.saveTimer = saveTimer
        self.importantAttr = importantAttr

        # Setup looping call to keep chute list perisistant only if reactor present
        if(self.reactor):
            self.repeater = self.reactor.LoopingCall(self.saveToDisk)
            self.repeater.start(self.saveTimer)

    def loadFromDisk(self):
        """Attempts to load the importantAttr from disk.
            Returns True if success, False otherwise."""
        
        if(pdos.exists(self.filename)):
            deleteFile = False
            out.info('-- %s Loading from disk\n' % logPrefix())
            data = ""
            try:
                pyld = pickle.load(pdos.open(self.filename, 'rb'))
                setattr(self, self.importantAttr, self.importAttr(pyld))
                return True
            except Exception as e:
                out.err('!! %s Error loading from disk: %s\n' % (logPrefix(), str(e)))
                deleteFile = True

            # Delete the file
            if(deleteFile):
                try:
                    pdos.unlink(self.filename)
                except Exception as e:
                    out.err('!! %s Error unlinking %s\n' % (logPrefix(), self.filename))
        
        return False
            
    def saveToDisk(self):
        """Saves the importantAttr to disk."""
        out.info('-- %s Saving to disk (%s)\n' % (logPrefix(), self.filename))
        
        # Make sure they want to save
        if(not self.attrSaveable()):
            return

        # Get whatever the data is
        pyld = self.exportAttr(getattr(self, self.importantAttr))
        
        # Write the file to disk, truncate if it exists
        try:
            pickle.dump(pyld, pdos.open(self.filename, 'wb'))
            pdos.syncFS()
            
        except Exception as e:
            out.err('!! %s Error writing to disk %s\n' % (logPrefix(), str(e)))
    
    def attrSaveable(self):
        """THIS SHOULD BE OVERRIDEN BY THE IMPLEMENTER."""
        return False
    
    def importAttr(self, pyld):
        """By default do nothing, but expect that this function could be overwritten"""
        return pyld
    
    def exportAttr(self, data):
        """By default do nothing, but expect that this function could be overwritten"""
        return data
