
from paradrop.lib.utils.output import out, logPrefix
from paradrop.lib.utils.pdutils import json2str, str2json, timeint, urlDecodeMe

from paradrop.lib.api.pdrest import APIDecorator
from paradrop.lib.api import pdapi

from paradrop.dock import deployment

#import wget
import os
#import zipfile


class ChuteAPI:

    """
    The Chute API submodule.
    This class handles all API calls related to actionable items that directly effect chutes.
    """

    def __init__(self, rest):
        self.rest = rest
        self.rest.register('POST', '^/v1/chute/create$', self.POST_createChute)
        self.rest.register('POST', '^/v1/chute/delete$', self.POST_deleteChute)

    @APIDecorator(requiredArgs=["config"])
    def POST_createChute(self, apiPkg):
        print 'STUFF STUFF STUFF'

        """
           Description:
           Arguments:
               POST request:
           Returns:
               On success: SUCCESS object
               On failure: FAILURE object
        """

        out.info('-- {} Creating chute...\n'.format(logPrefix()))
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
                'port_bindings': {80:9000},
                'restart_policy': {'MaximumRetryCount': 0, 'Name': "always"}
            }

        })

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
