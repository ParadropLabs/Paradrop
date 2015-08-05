####################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

'''
lib.utils.restart
Contains the functions required to restart chutes properly on power cycle of device.
Checks with pdconfd to make sure it was able to properly bring up all interfaces before
starting chutes.
'''

from pdtools.lib.output import out
from paradrop.backend.fc import chutestorage
from pdtools.lib.pdutils import timeint

def reloadChutes(configurer):
    chuteStore = chutestorage.ChuteStorage()
    chutes = [ ch for ch in chuteStore.getChuteList() if ch.state == 'running']

    for ch in chutes:
        update = dict(updateClass='CHUTE', updateType='restart', name=ch.name,
                      tok=timeint(), func=success ) #, pkg=apiPkg, func=self.rest.complete)

        configurer.updateList(**update)

def success(arg):
    print arg.failure
