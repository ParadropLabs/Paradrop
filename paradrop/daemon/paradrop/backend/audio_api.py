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
        pass

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

        pulse = pulsectl.Pulse()
        info = pulse.server_info()

        result = {
            'default_sink_name': info.default_sink_name,
            'default_source_name': info.default_source_name,
            'host_name': info.host_name,
            'server_name': info.server_name,
            'server_version': info.server_version,
            'user_name': info.user_name
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
               "name": "alsa_output.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-stereo",
               "volume": [1.5, 1.5]
             }
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        result = []

        pulse = pulsectl.Pulse()
        for sink in pulse.sink_list():
            result.append({
                'channel_count': sink.channel_count,
                'channel_list': sink.channel_list,
                'description': sink.description,
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

        pulse = pulsectl.Pulse()

        found = False
        for sink in pulse.sink_list():
            if sink.name == name:
                found = True
                break

        if found:
            volume = pulsectl.PulseVolumeInfo(body)
            pulse.volume_set(sink, volume)
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
               "name": "alsa_output.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-stereo.monitor",
               "volume": [1.0, 1.0]
             },
             {
               "channel_count": 1,
               "channel_list": ["mono"],
               "description": "PDP Audio Device Analog Mono",
               "name": "alsa_input.usb-Performance_Designed_Products_PDP_Audio_Device-00.analog-mono",
               "volume": [0.4298553466796875]
             }
           ]
        """
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')

        result = []

        pulse = pulsectl.Pulse()
        for source in pulse.source_list():
            result.append({
                'channel_count': source.channel_count,
                'channel_list': source.channel_list,
                'description': source.description,
                'name': source.name,
                'volume': source.volume.values
            })

        return json.dumps(result)
