import json

from pdtools.lib import nexus
from pdtools.lib.output import out
from pdtools.lib.pdutils import json2str, str2json, timeint, urlDecodeMe

from paradrop.backend.pdfcd.apiinternal import RouterSession
from paradrop.lib.api.pdrest import APIDecorator
from paradrop.lib.api import pdapi

from paradrop.lib.config import hostconfig

class ConfigAPI(object):
    """
    Configuration API.

    This class handles HTTP API calls related to router configuration.
    """
    def __init__(self, rest):
        self.rest = rest
        self.rest.register('GET', '^/v1/hostconfig', self.GET_hostconfig)
        self.rest.register('PUT', '^/v1/hostconfig', self.PUT_hostconfig)
        self.rest.register('GET', '^/v1/pdid', self.GET_pdid)
        self.rest.register('PUT', '^/v1/pdid', self.PUT_pdid)
        self.rest.register('PUT', '^/v1/apitoken', self.PUT_apitoken)
        self.rest.register('GET', '^/v1/provision', self.GET_provision)
        self.rest.register('POST', '^/v1/provision', self.POST_provision)

    @APIDecorator()
    def GET_hostconfig(self, apiPkg):
        """
        Query for router host configuration.

        Returns:
            an object containing host configuration.
        """
        config = hostconfig.prepareHostConfig()
        result = json.dumps(config, separators=(',',':'))
        apiPkg.request.setHeader('Content-Type', 'application/json')
        apiPkg.setSuccess(result)

    @APIDecorator(requiredArgs=["config"])
    def PUT_hostconfig(self, apiPkg):
        """
        Set the router host configuration.

        Arguments:
            config: object following same format as the GET result.
        Returns:
            an object containing message and success fields.
        """
        config = apiPkg.inputArgs.get('config')

        update = dict(updateClass='ROUTER', updateType='sethostconfig',
                name='__HOSTCONFIG__', tok=timeint(), pkg=apiPkg,
                hostconfig=config, func=self.rest.complete)
        self.rest.configurer.updateList(**update)

        apiPkg.request.setHeader('Content-Type', 'application/json')

        # Tell our system we aren't done yet (the configurer will deal with
        # closing the connection)
        apiPkg.setNotDoneYet()

    @APIDecorator()
    def GET_pdid(self, apiPkg):
        """
        Get the router identity (pdid).

        Returns the pdid as plain text or an empty string if it has not been
        set.
        """
        pdid = nexus.core.info.pdid
        if pdid is None:
            pdid = ""
        apiPkg.request.setHeader('Content-Type', 'text/plain')
        apiPkg.setSuccess(pdid)

    @APIDecorator(requiredArgs=["pdid"])
    def PUT_pdid(self, apiPkg):
        """
        Set the router identity (pdid).

        Arguments:
            pdid: a string (e.g. pd.lance.halo06)
        """
        pdid = apiPkg.inputArgs.get('pdid')
        nexus.core.provision(pdid, None)
        apiPkg.setSuccess("")

    @APIDecorator(requiredArgs=["apitoken"])
    def PUT_apitoken(self, apiPkg):
        """
        Set the router API token.

        Arguments:
            apitoken: a string
        """
        apitoken = apiPkg.inputArgs.get('apitoken')
        nexus.core.saveKey(apitoken, 'apitoken')
        apiPkg.setSuccess("")

    @APIDecorator()
    def GET_provision(self, apiPkg):
        """
        Get the provision status of this router.

        Returns a JSON object containing the following fields:
        pdid - (string or null) the router identity
        has_apitoken - (boolean) whether the router has an API token
        is_provisioned - (boolean) whether the router has been provisioned
        """
        status = dict()

        status['pdid'] = nexus.core.info.pdid

        apitoken = nexus.core.getKey('apitoken')
        status['has_apitoken'] = (apitoken is not None)

        status['is_provisioned'] = (status['pdid'] is not None \
                and status['has_apitoken'])

        apiPkg.request.setHeader('Content-Type', 'application/json')
        apiPkg.setSuccess(json.dumps(status, separators=(',',':')))

    @APIDecorator(requiredArgs=["pdid", "apitoken"])
    def POST_provision(self, apiPkg):
        """
        Provision the router.

        Provisioning assigns a name and keys used to connect to pdserver.

        Arguments:
            pdid: a string such as pd.lance.halo06
            apitoken: a string, token used to interact with pdserver
        """
        pdid = apiPkg.inputArgs.get('pdid')
        apitoken = apiPkg.inputArgs.get('apitoken')

        apiPkg.request.setHeader('Content-Type', 'text/plain')
        apiPkg.setNotDoneYet()

        changed = False
        if pdid != nexus.core.info.pdid:
            apiPkg.request.write("Changing pdid from {} to {}\n".format(
                    nexus.core.info.pdid, pdid))
            nexus.core.provision(pdid, None)
            changed = True
        if apitoken != nexus.core.getKey('apitoken'):
            apiPkg.request.write("Setting apitoken\n")
            nexus.core.saveKey(apitoken, 'apitoken')
            changed = True

        if changed:
            apiPkg.request.write("Initiating crossbar connection\n")

            def onConnected(session):
                apiPkg.request.write("Connected as {}\n".format(pdid))
                apiPkg.request.finish()
            def onFailure(error):
                apiPkg.request.write("Failed to connect: {}\n".format(error))
                apiPkg.request.finish()

            d = nexus.core.connect(RouterSession)
            d.addCallback(onConnected)
            d.addErrback(onFailure)

        else:
            apiPkg.request.write("Router is already provisioned as {}\n".format(pdid))
            apiPkg.request.finish()
