
from pdtools.lib.output import out
from io import BytesIO

"""
    dockerconfig module:
        This module contains all of the knowledge of how to take internal pdfcd
        representation of configurations of chutes and translate them into specifically
        what docker needs to function properly, whether that be in the form of dockerfiles
        or the HostConfig JSON object known at init time of the chute.
"""


def getVirtPreamble(update):
    out.warn('TODO implement me\n')
    if update.updateType == 'create':
        if not hasattr(update, 'dockerfile'):
            return
        if update.dockerfile is None:
            return
        else:
            out.info('Using prexisting dockerfile.\n')
            update.dockerfile = BytesIO(update.dockerfile.encode('utf-8'))
