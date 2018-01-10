"""
Manage audio input and output.

Endpoints for these functions can be found under /api/v1/audio.
"""

import json

from autobahn.twisted.resource import WebSocketResource
from klein import Klein
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

import pulsectl

from paradrop.base.output import out

from . import cors


class AudioApi(object):
    routes = Klein()

    def __init__(self):
        self.pulse = pulsectl.Pulse('paradrop-daemon')

    @routes.route('/info', methods=['GET'])
    def get_info(self, request):
        """
        Get audio server information.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/audio/info

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "default_sink_name": "alsa_output.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-stereo",
             "default_source_name": "alsa_input.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-mono",
             "host_name": "localhost.localdomain",
             "server_name": "pulseaudio",
             "server_version": "8.0-rebootstrapped",
             "user_name": "root"
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        info = self.pulse.server_info()
        result = {
            'default_sink_name': info.default_sink_name,
            'default_source_name': info.default_source_name,
            'host_name': info.host_name,
            'server_name': info.server_name,
            'server_version': info.server_version,
            'user_name': info.user_name
        }
        return json.dumps(result)

    @routes.route('/modules', methods=['GET'])
    def get_modules(self, request):
        """
        List loaded modules.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/audio/modules

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             { "index": 0, "n_used": 4294967295, "name": "module-device-restore" },
             { "index": 1, "n_used": 4294967295, "name": "module-stream-restore" },
             { "index": 2, "n_used": 4294967295, "name": "module-card-restore" },
             { "index": 3, "n_used": 4294967295, "name": "module-augment-properties" },
             ...
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        result = []
        for module in self.pulse.module_list():
            result.append({
                'index': module.index,
                'name': module.name,
                'n_used': module.n_used
            })

        return json.dumps(result)

    @routes.route('/modules', methods=['POST'])
    def load_module(self, request):
        """
        Load a module.

        **Example request**:

        .. sourcecode:: http

           POST /api/v1/audio/modules

           {
             "name": "module-switch-on-connect"
           }

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           {
             "index": 21,
             "name": "module-switch-on-connect"
           }
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        body = json.loads(request.content.read())

        index = self.pulse.module_load(body['name'])
        result = {
            'index': index,
            'name': body['name']
        }
        return json.dumps(result)

    @routes.route('/sinks', methods=['GET'])
    def get_sinks(self, request):
        """
        List sinks.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/audio/sinks

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             {
               "channel_count": 2,
               "channel_list": ["front-left", "front-right"],
               "description": "PDP Audio Device Analog Stereo",
               "index": 0,
               "name": "alsa_output.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-stereo",
               "volume": [1.5, 1.5]
             }
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        result = []
        for sink in self.pulse.sink_list():
            result.append({
                'channel_count': sink.channel_count,
                'channel_list': sink.channel_list,
                'description': sink.description,
                'index': sink.index,
                'name': sink.name,
                'volume': sink.volume.values
            })

        return json.dumps(result)

    @routes.route('/sinks/<string:name>/volume', methods=['PUT'])
    def set_sink_volume(self, request, name):
        """
        Set sink volume.

        **Example request**:

        .. sourcecode:: http

           PUT /api/v1/audio/sinks/alsa_output.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-stereo/volume

           [1.0, 1.0]

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [1.0, 1.0]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        body = json.loads(request.content.read())

        found = False
        for sink in self.pulse.sink_list():
            if sink.name == name:
                found = True
                break

        if found:
            volume = pulsectl.PulseVolumeInfo(body)
            self.pulse.volume_set(sink, volume)
            return json.dumps(body)
        else:
            request.setResponseCode(404)
            return '{}'

    @routes.route('/sources', methods=['GET'])
    def get_sources(self, request):
        """
        List audio sources.

        **Example request**:

        .. sourcecode:: http

           GET /api/v1/audio/sources

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [
             {
               "channel_count": 2,
               "channel_list": ["front-left", "front-right"],
               "description": "Monitor of PDP Audio Device Analog Stereo",
               "index": 0,
               "name": "alsa_output.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-stereo.monitor",
               "volume": [1.0, 1.0]
             },
             {
               "channel_count": 1,
               "channel_list": ["mono"],
               "description": "PDP Audio Device Analog Mono",
               "index": 1,
               "name": "alsa_input.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-mono",
               "volume": [0.4298553466796875]
             }
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        result = []
        for source in self.pulse.source_list():
            result.append({
                'channel_count': source.channel_count,
                'channel_list': source.channel_list,
                'description': source.description,
                'index': source.index,
                'name': source.name,
                'volume': source.volume.values
            })

        return json.dumps(result)

    @routes.route('/sources/<string:name>/volume', methods=['PUT'])
    def set_source_volume(self, request, name):
        """
        Set source volume.

        **Example request**:

        .. sourcecode:: http

           PUT /api/v1/audio/sources/alsa_input.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-mono/volume

           [1.0]

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json

           [1.0]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        body = json.loads(request.content.read())

        found = False
        for source in self.pulse.source_list():
            if source.name == name:
                found = True
                break

        if found:
            volume = pulsectl.PulseVolumeInfo(body)
            self.pulse.volume_set(source, volume)
            return json.dumps(body)
        else:
            request.setResponseCode(404)
            return '{}'
