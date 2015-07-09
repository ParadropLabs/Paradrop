
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
        print 'here'
        #preamble setup
        dockerfile = 'FROM ' + update.image
        dockerfile += '\nMAINTAINER ' + update.owner

        #setup commands
        for run in update.setup:
            dockerfile += '\nRUN ' + run

        for f in update.addFile:
            dockerfile += '\nADD ' + f
        dockerfile += '\nEXPOSE 80'

        #Launch command
        if(update.init != None):
            dockerfile += '\nCMD ["' + update.init + '"]'

        #encode into fileobj
        update.dockerfile = BytesIO(dockerfile.encode('utf-8'))
    
    
def getVirtDHCPSettings(update):
    out.warn('** %s TODO implement me\n' % logPrefix())

def setVirtDHCPSettings(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
