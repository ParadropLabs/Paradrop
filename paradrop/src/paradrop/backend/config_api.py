import json
from klein import Klein
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

from paradrop.base import nexus, status
from paradrop.base.pdutils import timeint, str2json
from paradrop.lib.config import hostconfig
from paradrop.lib.misc.reporting import sendStateReport
from paradrop.lib.utils.http import PDServerRequest

from apiinternal import RouterSession
from apibridge import updateManager
from . import cors

class ConfigApi(object):
    """
    Configuration API.
    This class handles HTTP API calls related to router configuration.
    
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

    routes = Klein()

    def __init__(self, update_manager):
        self.update_manager = update_manager

    @routes.route('/hostconfig', methods=['PUT'])
    @inlineCallbacks
    def update_hostconfig(self, request):
        cors.enable_cors(request)
        body = str2json(request.content.read())
        config = body['config']
        if config:
            update = dict(updateClass='ROUTER',
                          updateType='sethostconfig',
                          name='__PARADROP__',
                          tok=timeint(),
                          hostconfig=config)
            result = yield self.update_manager.add_update(**update)
            request.setHeader('Content-Type', 'application/json')
            returnValue(json.dumps(result))
        else:
            returnValue(None)


    @routes.route('/hostconfig')
    def get_hostconfig(self, request):
        cors.enable_cors(request)
        config = hostconfig.prepareHostConfig()
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(config, separators=(',',':'))


    @routes.route('/pdid')
    def get_pdid(self, request):
        cors.enable_cors(request)
        pdid = nexus.core.info.pdid
        if pdid is None:
            pdid = ""
        request.setHeader('Content-Type', 'application/json')
        return json.dumps({'pdid': pdid})


    @routes.route('/provision', methods=['POST'])
    def provision(self, request):
        cors.enable_cors(request)
        body = str2json(request.content.read())
        routerId = body['routerId']
        apitoken = body['apitoken']
        pdserver = body['pdserver']
        wampRouter = body['wampRouter']

        changed = False
        if routerId != nexus.core.info.pdid \
            or pdserver != nexus.core.info.pdserver \
            or wampRouter != nexus.core.info.wampRouter:
            if pdserver and wampRouter:
                nexus.core.provision(routerId, pdserver, wampRouter)
            else:
                nexus.core.provision(routerId)
            changed = True

        if apitoken != nexus.core.getKey('apitoken'):
            nexus.core.saveKey(apitoken, 'apitoken')
            changed = True

        if changed:
            PDServerRequest.resetToken()
            status.apiTokenVerified = False
            status.wampConnected = False

            def sessionCallback(session):
                sendStateReport()
                updateManager.startUpdate()

            def sendResponse(result):
                result = dict()
                result['provisioned'] = True
                result['httpConnected'] = status.apiTokenVerified
                result['wampConnected'] = status.wampConnected
                request.setHeader('Content-Type', 'application/json')
                return json.dumps(result)

            d = nexus.core.connect(RouterSession)
            d.addCallback(sessionCallback)
            d.addTimeout(6, reactor).addBoth(sendResponse)


    @routes.route('/provision')
    def get_provision(self, request):
        cors.enable_cors(request)
        result = dict()
        result['routerId'] = nexus.core.info.pdid
        result['pdserver'] = nexus.core.info.pdserver
        result['wampRouter'] = nexus.core.info.wampRouter
        apitoken = nexus.core.getKey('apitoken')
        result['provisioned'] = (result['routerId'] is not None and \
                                 apitoken is not None)
        result['httpConnected'] = status.apiTokenVerified
        result['wampConnected'] = status.wampConnected

        request.setHeader('Content-Type', 'application/json')
        return json.dumps(result)


    @routes.route('/startUpdate', methods=['POST'])
    def start_update(self, request):
        pass


    @routes.route('/factoryReset', methods=['POST'])
    def factory_reset(self, request):
        pass
