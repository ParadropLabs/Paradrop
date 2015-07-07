
from paradrop.lib.utils.output import out, logPrefix
from paradrop.lib.utils.pdutils import json2str, str2json, timeint, urlDecodeMe

from paradrop.lib.api.pdrest import APIDecorator
from paradrop.lib.api import pdapi

import wget


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
        print apiPkg.inputArgs['url']
        path = downloadChute(apiPkg.inputArgs['url'])
        installChute(path)
        startDockerContainer(path)

        # For now fake out a create chute message
        self.rest.configurer.updateList(updateClass='CHUTE', updateType='create',
                                        tok=timeint(), name='TheName', config='Stuff and Things',
                                        pkg=apiPkg, func=self.rest.complete)

        # Tell our system we aren't done yet (the configurer will deal with
        # closing the connection)
        apiPkg.setNotDoneYet()


#########
# I do not belong here. Find me a home, please.
#########


def downloadChute(url):
    # output = os.environ['TMPDIR']

    # local testing
    output = os.getcwd() + '/buildenv'

    wget.download(url, out=output + '/inbound')


def installChute(path):
    pass


def startDockerContainer(path):
    pass
