
from pdtools.lib.output import out
from pdtools.lib.pdutils import json2str, str2json, timeint, urlDecodeMe

from paradrop.lib.api.pdrest import APIDecorator
from paradrop.lib.api import pdapi

class ChuteAPI:

    """
    The Chute API submodule.
    This class handles all API calls related to actionable items that directly effect chutes.
    """

    def __init__(self, rest):
        self.rest = rest
        self.rest.register('POST', '^/v1/chute/create$', self.POST_createChute)
        self.rest.register('POST', '^/v1/chute/delete$', self.POST_deleteChute)
        self.rest.register('POST', '^/v1/chute/stop$', self.POST_stopChute)
        self.rest.register('POST', '^/v1/chute/start$', self.POST_startChute)

    @APIDecorator(requiredArgs=["config"])
    def POST_createChute(self, apiPkg):
        """
           Description:
           Arguments:
               POST request:
           Returns:
               On success: SUCCESS object
               On failure: FAILURE object
        """

        out.info('Creating chute...')
        # For now fake out a create chute message
        update = dict(updateClass='CHUTE', updateType='create',
                      tok=timeint(), pkg=apiPkg, func=self.rest.complete)

        update.update(apiPkg.inputArgs.get('config'))
        self.rest.configurer.updateList(**update)

        # Tell our system we aren't done yet (the configurer will deal with
        # closing the connection)
        apiPkg.setNotDoneYet()

    @APIDecorator(requiredArgs=["name"])
    def POST_deleteChute(self, apiPkg):
        """
           Description:
           Arguments:
               POST request:
           Returns:
               On success: SUCCESS object
               On failure: FAILURE object
        """

        out.info('Deleting chute...')

        # For now fake out a create chute message
        update = dict(updateClass='CHUTE', updateType='delete', name=apiPkg.inputArgs.get('name'),
                      tok=timeint(), pkg=apiPkg, func=self.rest.complete)

        self.rest.configurer.updateList(**update)

        # Tell our system we aren't done yet (the configurer will deal with
        # closing the connection)
        apiPkg.setNotDoneYet()

    @APIDecorator(requiredArgs=["name"])
    def POST_startChute(self, apiPkg):
        """
           Description:
           Arguments:
               POST request:
           Returns:
               On success: SUCCESS object
               On failure: FAILURE object
        """

        out.info('Starting chute...')

        # For now fake out a create chute message
        update = dict(updateClass='CHUTE', updateType='start', name=apiPkg.inputArgs.get('name'),
                      tok=timeint(), pkg=apiPkg, func=self.rest.complete)

        self.rest.configurer.updateList(**update)

        # Tell our system we aren't done yet (the configurer will deal with
        # closing the connection)
        apiPkg.setNotDoneYet()

    @APIDecorator(requiredArgs=["name"])
    def POST_stopChute(self, apiPkg):
        """
           Description:
           Arguments:
               POST request:
           Returns:
               On success: SUCCESS object
               On failure: FAILURE object
        """

        out.info('Stopping chute...')

        # For now fake out a create chute message
        update = dict(updateClass='CHUTE', updateType='stop', name=apiPkg.inputArgs.get('name'),
                      tok=timeint(), pkg=apiPkg, func=self.rest.complete)

        self.rest.configurer.updateList(**update)

        # Tell our system we aren't done yet (the configurer will deal with
        # closing the connection)
        apiPkg.setNotDoneYet()
