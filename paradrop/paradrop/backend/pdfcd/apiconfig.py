import json
from twisted.internet import reactor

from pdtools.lib import nexus
from pdtools.lib.output import out
from pdtools.lib.pdutils import json2str, str2json, timeint, urlDecodeMe

from paradrop.backend.pdfcd.apiinternal import RouterSession
from paradrop.lib.api.pdrest import APIDecorator
from paradrop.lib.api import pdapi

from paradrop.lib.config import hostconfig
from paradrop.backend.pdfcd.apibridge import updateManager
from paradrop.lib.reporting import sendStateReport

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
                name='__PARADROP__', tok=timeint(), pkg=apiPkg,
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

    @APIDecorator(requiredArgs=["pdid", "apitoken", "wamppassword"])
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
        wamppassword = apiPkg.inputArgs.get('wamppassword')

        apiPkg.request.setHeader('Content-Type', 'text/plain')

        changed = False
        if pdid != nexus.core.info.pdid:
            nexus.core.provision(pdid, None)
            changed = True
        if apitoken != nexus.core.getKey('apitoken'):
            nexus.core.saveKey(apitoken, 'apitoken')
            changed = True
        if wamppassword != nexus.core.getKey('wamppassword'):
            nexus.core.saveKey(wamppassword, 'wamppassword')
            changed = True

        if changed:
            # the API token is used to authenticate both HTTP and WAMP

            def onFailure(error):
                result = dict()
                result['provisioned'] = True
                result['connected'] = False
                result['error'] = error
                apiPkg.request.write(json.dumps(result))
                apiPkg.request.finish()

            # The router might try to connect to the backend server continuously,
            # and we will never get errback
            # We have to response the request somehow...
            callId = reactor.callLater(2, onFailure, 'timeout')

            def onConnected(session):
                callId.cancel()

                result = dict()
                result['provisioned'] = True
                result['connected'] = True
                apiPkg.request.write(json.dumps(result))
                apiPkg.request.finish()

            d = nexus.core.connect(RouterSession)
            d.addCallback(onConnected)
            d.addErrback(onFailure)

            # Set up communication with pdserver.
            # 1. Create a report of the current system state and send that.
            # 2. Poll for a list of updates that should be applied.
            sendStateReport()
            updateManager.startUpdate()

            apiPkg.setNotDoneYet()

        else:
            apiPkg.setFailure(pdapi.ERR_BADPARAM, "Router is already provisioned as {}: %s\n".format(pdid))
