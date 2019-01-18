"""
    dockerconfig module:
        This module contains all of the knowledge of how to take internal pdfcd
        representation of configurations of chutes and translate them into specifically
        what docker needs to function properly, whether that be in the form of dockerfiles
        or the HostConfig JSON object known at init time of the chute.
"""

import os
import random
from io import BytesIO

from paradrop.base.output import out
from paradrop.base import settings
from paradrop.core.container import dockerapi
from paradrop.lib.utils import pdos, pdosq


def generateToken(bits=128):
    return "{:x}".format(random.getrandbits(bits))


def getVirtPreamble(update):
    """
    Prepare various settings for Docker containers.
    """
    extDataDir = settings.EXTERNAL_DATA_DIR.format(chute=update.new.name)
    extDataDir = os.path.expanduser(extDataDir)
    intDataDir = getattr(update.new, 'dataDir', settings.INTERNAL_DATA_DIR)

    extSystemDir = settings.EXTERNAL_SYSTEM_DIR.format(chute=update.new.name)
    extSystemDir = os.path.expanduser(extSystemDir)
    intSystemDir = getattr(update.new, 'systemDir', settings.INTERNAL_SYSTEM_DIR)

    volumes = {
        extDataDir: {
            'bind': intDataDir,
            'mode': 'rw'
        },

        extSystemDir: {
            'bind': intSystemDir,
            'mode': 'ro'
        }
    }

    # Prepare port bindings while there might still be an old version of the
    # chute running so that we can inherit any dynamic port settings.
    for service in update.new.get_services():
        bindings = dockerapi.prepare_port_bindings(service)
        update.cache_set("portBindings:{}".format(service.name), bindings)

    update.cache_set('volumes', volumes)
    update.cache_set('internalDataDir', intDataDir)
    update.cache_set('externalDataDir', extDataDir)
    update.cache_set('internalSystemDir', intSystemDir)
    update.cache_set('externalSystemDir', extSystemDir)

    # Reuse previous token if it exists. This is not ideal but works for
    # updates that do not recreate the container with updated environment
    # variables. Stop then start is one such sequence where environment
    # variables are not updated.
    token = None
    if update.old is not None:
        token = update.old.getCache('apiToken')
    if token is None:
        token = generateToken()
    update.cache_set('apiToken', token)

    # Deprecated: we set these values in the chute cache here because there is
    # still code that depends on reading this from the chute storage.  This can
    # be removed when the corresponding call to getCache is removed.
    update.new.setCache('externalSystemDir', extSystemDir)
    update.new.setCache('apiToken', token)

    if not hasattr(update, 'dockerfile'):
        return
    if update.dockerfile is None:
        return
    else:
        out.info('Using prexisting dockerfile.\n')
        update.dockerfile = BytesIO(update.dockerfile.encode('utf-8'))


def createVolumeDirs(update):
    """
    Create directories required by the chute.
    """
    extDataDir = update.cache_get('externalDataDir')
    extSystemDir = update.cache_get('externalSystemDir')

    if update.updateType == 'delete':
        pdos.remove(extDataDir, suppressNotFound=True)
        pdos.remove(extSystemDir, suppressNotFound=True)
    else:
        pdosq.makedirs(extDataDir)
        pdosq.makedirs(extSystemDir)
        try:
            os.chown(extDataDir, settings.CONTAINER_UID, -1)
        except:
            # chown is not permitted in strict confinement.
            # TODO: do we need to chmod the data directory, or does it work
            # fine regardless?
            pass


def abortCreateVolumeDirs(update):
    # If there is no old version of the chute, then clean up directories that
    # we created.  Otherwise, leave them in place for the old version.
    if update.old is None:
        extDataDir = update.cache_get('externalDataDir')
        pdos.remove(extDataDir)

        extSystemDir = update.cache_get('externalSystemDir')
        pdos.remove(extSystemDir)
