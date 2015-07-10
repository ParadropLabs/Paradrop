
from paradrop.lib.utils.output import out, logPrefix
from io import BytesIO

"""
    dockerconfig module:
        This module contains all of the knowledge of how to take internal pdfcd
        representation of configurations of chutes and translate them into specifically
        what docker needs to function properly, whether that be in the form of dockerfiles
        or the HostConfig JSON object known at init time of the chute.
"""


def getVirtPreamble(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    if(update.updateType == 'create'):
        if(not hasattr(update, 'dockerfile')):
            return
        if(update.dockerfile == None):
            return
        else:
            out.info('-- %s Using prexisting dockerfile.\n' % logPrefix())
            update.dockerfile = BytesIO(update.dockerfile.encode('utf-8'))
    
    
def getVirtDHCPSettings(update):
    out.warn('** %s TODO implement me\n' % logPrefix())

def setVirtDHCPSettings(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
