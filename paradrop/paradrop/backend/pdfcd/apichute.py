
from pdtools.lib.output import out
from pdtools.lib.pdutils import json2str, str2json, timeint, urlDecodeMe

from paradrop.lib.api.pdrest import APIDecorator
from paradrop.lib.api import pdapi

from paradrop.dock import deployment


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
        import datetime
        update.update({
            'from': 'ubuntu', 'name': 'helloworld',
            'firewall': [{'type': 'redirect', 'from': '@host.lan:9000\n',
                          'name': 'web-access', 'to': '*mylan:80\n'}],
            'setup': [{'program': 'echo', 'args': '"<html><h1>This is working!</h1></html>" > index.html\n'}],
            'owner': 'dale',
            'init': [{'program': 'python', 'args': '-m SimpleHTTPServer 80'}],
            'date': datetime.date(2015, 7, 7),
            'net': {'mylan': {'intfName': 'eth0', 'type': 'lan', 'ipaddr': '192.168.17.5', 'netmask': '255.255.255.0'}},
            'description': 'This is a very very simple hello world chute.\n',
            'dockerfile': '''
            FROM ubuntu
            MAINTAINER Nick Hyatt
            RUN echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
            RUN apt-get update
            RUN apt-get -y install nginx

            RUN echo "daemon off;" >> /etc/nginx/nginx.conf
            RUN mkdir /etc/nginx/ssl
            ADD https://raw.githubusercontent.com/nphyatt/docker-test/master/default /etc/nginx/sites-available/default
            ADD https://raw.githubusercontent.com/nphyatt/docker-test/master/index.html /var/www/index.html
            RUN chmod 664 /var/www/index.html
            RUN chmod 664 /etc/nginx/sites-available/default

            EXPOSE 80

            CMD ["nginx"]
            ''',
            'host_config': {
                'port_bindings': {80: 9000},
                'restart_policy': {'MaximumRetryCount': 0, 'Name': "always"}
            }

        })

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

        # TODO implement

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
