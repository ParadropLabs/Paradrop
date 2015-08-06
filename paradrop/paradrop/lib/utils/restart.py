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
from pdtools.lib.pdutils import json2str, str2json, timeint, urlDecodeMe
from paradrop.backend.pdconfd.client import waitSystemUp
from paradrop.lib import chute
import time

def reloadChutes():
    chuteStore = chutestorage.ChuteStorage()
    chutes = [ ch for ch in chuteStore.getChuteList() if ch.state == 'running']

    #We need to make sure confd is up and all interfaces have been brought up properly
    confdup = False
    while not confdup:
        confdInfo = waitSystemUp()
        if confdInfo == None:
            time.sleep(1)
            continue
        confdup = True
        confdInfo = str2json(confdInfo)

    #Remove any chutes from the restart queue if confd failed to bring up the proper interfaces
    failedChutes = []
    for iface in confdInfo:
        if iface.get('success') == False:
            while iface.get('comment') in chutes: 
                #TODO stop the chute and add error message to it
                chutes.remove(iface.get('comment'))
            if iface.get('comment') not in failedChutes:
                failedChutes.append(iface.get('comment'))

    #First stop all chutes that failed to bring up interfaces according to pdconfd then start successful ones
    #We do this because pdfcd needs to handle cleaning up uci files and then tell pdconfd 
    updates = []
    for ch in failedChutes:
        update = dict(updateClass='CHUTE', updateType='stop', name=ch,
                      tok=timeint(), func=failure, warning=chute.FAILURE_WARNING) #, pkg=apiPkg, func=self.rest.complete)
        updates.append(update)

    for ch in chutes:
        update = dict(updateClass='CHUTE', updateType='restart', name=ch.name,
                      tok=timeint(), func=success ) #, pkg=apiPkg, func=self.rest.complete)
        updates.append(update)

    return updates

def success(arg):
    print arg.__dict__

def failure(arg):
    print arg.__dict__
