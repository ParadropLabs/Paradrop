
from paradrop.lib.utils.output import out, logPrefix
from paradrop.lib.utils.pdutils import json2str, str2json, timeint, urlDecodeMe

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

    @APIDecorator(requiredArgs=["test"])
    def POST_createChute(self, apiPkg):
        """
           Description:
           Arguments:
               POST request:
           Returns:
               On success: SUCCESS object
               On failure: FAILURE object
        """

        out.info('-- {} Creating chute...\n'.format(logPrefix()))

        # TODO implement

        # For now fake out a create chute message
        update = dict(updateClass='CHUTE', updateType='create',
                        tok=timeint(), pkg=apiPkg, func=self.rest.complete)
        import datetime
        update.update({
            'from': 'ubuntu', 'name': 'helloworld',
            'firewall': [{'type': 'redirect', 'from': '@host.lan:5000\n',
            'name': 'web-access', 'to': '*mylan:80\n'}],
            'setup': [{'program': 'echo',
            'args': '"<html><h1>This is working!</h1></html>" > index.html\n'}],
            'owner': 'dale',
            'init': [{'program': 'python', 'args': '-m SimpleHTTPServer 80'}],
            'date': datetime.date(2015, 7, 7),
            'net': {'mylan': {'intfName': 'eth0', 'type': 'lan'}},
            'description': 'This is a very very simple hello world chute.\n'})
        
        self.rest.configurer.updateList(**update)

        # Tell our system we aren't done yet (the configurer will deal with
        # closing the connection)
        apiPkg.setNotDoneYet()
    
    @APIDecorator(requiredArgs=["test"])
    def POST_deleteChute(self, apiPkg):
        """
           Description:
           Arguments:
               POST request:
           Returns:
               On success: SUCCESS object
               On failure: FAILURE object
        """

        out.info('-- {} Deleting chute...\n'.format(logPrefix()))

        # TODO implement

        # For now fake out a create chute message
        update = dict(updateClass='CHUTE', updateType='delete', name='helloworld',
                        tok=timeint(), pkg=apiPkg, func=self.rest.complete)
        
        self.rest.configurer.updateList(**update)

        # Tell our system we aren't done yet (the configurer will deal with
        # closing the connection)
        apiPkg.setNotDoneYet()
