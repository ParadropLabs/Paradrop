
from paradrop.lib.utils.output import out, logPrefix
from paradrop.lib.utils.pdutils import json2str, str2json, timeint, urlDecodeMe

from paradrop.lib.api.pdrest import APIDecorator
from paradrop.lib.api import pdapi

from paradrop.dock import deployment

import wget
import os
import zipfile


class ChuteAPI:

    """
    The Chute API submodule.
    This class handles all API calls related to actionable items that directly effect chutes.
    """

    def __init__(self, rest):
        self.rest = rest
        self.rest.register('POST', '^/v1/chute/create$', self.POST_createChute)

    @APIDecorator(requiredArgs=["url"])
    def POST_createChute(self, apiPkg):
        print 'STUFF STUFF STUFF'

        """
           Description:
               Get the network config of all chutes under an AP  from the vnet_network table
           Arguments:
               POST request:
                  @test
           Returns:
               On success: SUCCESS object
               On failure: FAILURE object
        """

        out.info('-- {} Creating chute...\n'.format(logPrefix()))

        # download and install the chute with docker
        # TODO: handle errors that arise from docker. Make this async

        name = 'testchute'

        print ''
        print apiPkg.inputArgs['url']
        print ''

        zipName = apiPkg.inputArgs['url'] + '/archive/master.zip'

        path = downloadChute(zipName, name)
        installChute(path, name)
        startDockerContainer(path, name)

        # For now fake out a create chute message
        self.rest.configurer.updateList(updateClass='CHUTE', updateType='create',
                                        tok=timeint(), name=name, config='Stuff and Things',
                                        pkg=apiPkg, func=self.rest.complete)

        # TODO: cleanup download directory

        # Tell our system we aren't done yet (the configurer will deal with
        # closing the connection)
        apiPkg.setNotDoneYet()


#########
# I do not belong here. Find me a home, please.
#########

def downloadChute(url, name):
    '''
    Downloads a chute as a zip from the provided URL, unzips it, 
    removes the zip, and returns the path to the contents of the chute.

    This method blocks on both wget and zipfile. It must be made asynchronous.
    '''

    outPath = os.path.dirname(os.getcwd()) + '/buildenv/inbound/'  # local testing
    # outPath = os.environ['TMPDIR']
    zipPath = outPath + name + '.zip'
    chutePath = outPath + name

    if not os.path.exists(outPath):
        os.makedirs(outPath)

    wget.download(url, out=zipPath)

    # unzip contents
    zipped = zipfile.ZipFile(zipPath)
    zipped.extractall(path=chutePath)
    zipped.close()
    os.remove(zipPath)

    return chutePath + '/' + os.listdir(chutePath)[0]


def installChute(path, name):
    '''
    Parse config file, make necesary changes to the system-- any and all paradrop-related config.
    '''
    pass


def startDockerContainer(path, name):
    '''
    Start the docker container given a directory containing the application.

    Configure port bindings based on the conf files. Could merge this method and the above
    depending on how complicated it gets

    Blocks badly. Needs to be fixed.
    '''
    deployment.launchApp(path=path, name=name, restart_policy={"MaximumRetryCount": 0, "Name": "always"},
                         port_bindings={80: 9000})
