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
from paradrop.lib import status

from .apibridge import updateManager


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
        self.rest.register('POST', '^/v1/startUpdate', self.POST_startUpdate)

    """
    Hostconfig example:
    {
        "lan": {
            "dhcp": {
                "leasetime": "12h",
                "limit": 100,
                "start": 100
            },
            "interfaces": [
                "eth1",
                "eth2"
            ],
            "ipaddr": "192.168.1.1",
            "netmask": "255.255.255.0",
            "proto": "static"
        },
        "wan": {
            "interface": "eth0",
            "proto": "dhcp"
        },
        "wifi": [
            {
                "channel": 1,
                "interface": "wlan0"
            },
            {
                "channel": 36,
                "interface": "wlan1",
                "hwmode": "11a",
                "htmode": "HT40+",
                "short_gi_40": true
            }
        ],
        "wifi-interfaces": [
            {
                "device": "wlan0",
                "ssid": "paradrop",
                "mode": "ap",
                "network": "lan",
                "ifname": "wlan0"
            },
            {
                "device": "wlan1",
                "ssid": "paradrop-5G",
                "mode": "ap",
                "network": "lan",
                "ifname": "wlan1"
            }
        ]
    }

    The "wifi" section sets up physical device settings.
    Right now it is just the channel number.
    Other settings related to 11n or 11ac may go there as we implement them.

    The "wifi-interfaces" section sets up virtual interfaces.  Each virtual
    interface has an underlying physical device, but there can be multiple
    interfaces per device up to a limit set somewhere in the driver,
    firmware, or hardware.  Virtual interfaces can be configured as APs as
    in the example. They could also be set to client mode and connect to
    other APs, but this is not supported currently.

    Therefore, it enables one card in the sense that it starts an AP using
    one of the cards but does not start anything on the second card.  On the
    other hand, it enables two cards in the sense that it configures one
    card to use channel 1 and the second one to use channel 6, and a chute
    may start an AP on the second card.

    Here are a few ways we can modify the example configuration:
    - If we want to run a second AP on the second device, we can add a
      section to wifi-interfaces with device="wlan1" and ifname="wlan1".
    - If we want to run a second AP on the first device, we can add a
      section to wifi-interfaces with device="wlan0" and an ifname that is
      different from all others interfaces sharing the device.
      We should avoid anything that starts with "wlan" except the case
      where the name exactly matches the device.
      For device "wlan0", acceptable names would be "wlan0", "pd-wlan", etc.
      Avoid "vwlan0.X" and the like because that would conflict with chute interfaces,
      but "hwlan0.X" would be fine.
    - If we want to add WPA2, set encryption="psk2" and key="the passphrase"
      in the wifi-interface section for the AP.
      Based on standard, the Passphrase of WPA2 must be between 8 and 63 characters, inclusive.

    Advanced wifi device settings:
    - For 2.4 GHz channels, set hwmode="11g", and for 5 GHz, set hwmode="11a".
    It may default to 802.11b (bad, slow) otherwise.
    - For a 40 MHz channel width in 802.11n, set htmode="HT40+" or htmode="HT40-".
    Plus means add the next higher channel, and minus means add the lower channel.
    For example, setting channel=36 and htmode="HT40+" results in using
    channels 36 and 40.
    - If the hardware supports it, you can enable short guard interval
    for slightly higher data rates.  There are separate settings for each
    channel width, short_gi_20, short_gi_40, short_gi_80, short_gi_160.
    Most 11n hardware can support short_gi_40 at the very least.
    """
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
        result = dict()

        result['pdid'] = nexus.core.info.pdid

        apitoken = nexus.core.getKey('apitoken')
        result['provisioned'] = (result['pdid'] and \
                                 apitoken is not None)
        result['http_connected'] = status.apiTokenVerified
        result['wamp_connected'] = status.wampConnected

        apiPkg.request.setHeader('Content-Type', 'application/json')
        apiPkg.setSuccess(json.dumps(result, separators=(',',':')))

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

        changed = False
        if pdid != nexus.core.info.pdid:
            nexus.core.provision(pdid, None)
            changed = True
        if apitoken != nexus.core.getKey('apitoken'):
            nexus.core.saveKey(apitoken, 'apitoken')
            changed = True

        if changed:
            # the API token is used to authenticate both HTTP and WAMP

            def onFailure(error):
                result = dict()
                result['provisioned'] = True
                result['http_connected'] = status.apiTokenVerified
                result['wamp_connected'] = status.wampConnected
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
                result['http_connected'] = status.apiTokenVerified
                result['wamp_connected'] = status.wampConnected
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

    @APIDecorator()
    def POST_startUpdate(self, apiPkg):
        """
        Start polling for updates from pdserver.

        This triggers an immediate poll, which could be useful to manually
        trigger an update if the automatic mechanisms are not working (e.g.
        when testing with an incomplete server setup).
        """
        updateManager.startUpdate()

        apiPkg.request.setHeader('Content-Type', 'text/plain')
        apiPkg.setSuccess("OK")
