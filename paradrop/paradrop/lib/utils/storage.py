###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import json, os

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
                with pdos.open(self.filename, 'r') as fd:
                    while(True):
                        line = fd.readline().rstrip().rstrip('\n')
                        if(not line):
                            break
                        data += line
            except Exception as e:
                out.err('!! %s Error loading from disk: %s\n' % (logPrefix(), str(e)))
                deleteFile = True
            
            try:
                # Now we have the string in @data, jsonize it
                tmp = json.loads(data, object_hook=pdutils.convertUnicode)
                
                # JSON should contain a hash and a payload of the data
                resp = pdutils.check(tmp, dict, valMatches={'hash':int, 'payload':str})
                if(resp):
                    out.err('!! %s Error: %s\n' % (logPrefix(), resp))
                    deleteFile = True
                
                # Verify the hash
                else:
                    theHash = tmp['hash']
                    pyld = tmp['payload']
                    tmpHash = hash(pyld)
                    
                    if(theHash != tmpHash):
                        out.err("!! %s Hashes don't match\n" % (logPrefix()))
                        deleteFile = True
                    else:
                        out.verbose('-- %s Loaded from file successfully.\n' % logPrefix())
                        # Set the attr here
                        setattr(self, self.importantAttr, self.importAttr(pyld))
                        return True

            # if we get any error JSONizing it we should really delete it b/c its corrupt
            except Exception as e:
                out.err('!! %s Error JSON.loads: %s\n' % (logPrefix(), str(e)))
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
        theAttr = getattr(self, self.importantAttr)
        
        # Do prep work first so the file is open as little as possible
        pyld = self.exportAttr(theAttr)
        if(not isinstance(pyld, str)):
            out.err('!! %s Unable to hash attr, must be str type\n' % (logPrefix()))
            return
        tmpHash = hash(pyld)
            
        tmpJson = {'hash': tmpHash, 'payload': pyld}
        
        # Write the file to disk, truncate if it exists
        try:
            # Make last char newline, easier to read and write out
            output = json.dumps(tmpJson) + "\n"
            fd = pdos.open(self.filename, 'w')
            fd.write(output)
            
            # Make sure to flush it to disk (you need both of these calls)
            fd.flush()
            os.fsync(fd.fileno())

            # Close the file
            fd.close()
            
        except Exception as e:
            out.err('!! %s Error writing to disk %s\n' % (logPrefix(), str(e)))
    
    def attrSaveable(self):
        """THIS SHOULD BE OVERRIDEN BY THE IMPLEMENTER."""
        return False
    
    def importAttr(self, pyld):
        """THIS SHOULD BE OVERRIDEN BY THE IMPLEMENTER."""
        return pyld
    
    def exportAttr(self, data):
        """THIS SHOULD BE OVERRIDEN BY THE IMPLEMENTER."""
        return data
