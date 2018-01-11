import json

from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.backend import audio_api


class TestChuteApi(object):
    def __init__(self):
        self.pulse = MagicMock()
        self.api = audio_api.AudioApi()

    def setUp(self):
        patcher = patch("paradrop.backend.audio_api.pulsectl")
        pulsectl = patcher.start()

        pulsectl.Pulse.return_value = self.pulse
        self.pulse.__enter__.return_value = self.pulse

    def test_get_info(self):
        request = MagicMock()

        info = MagicMock()
        info.default_sink_name = "test"
        info.server_name = "test"
        info.default_source_name = "test"
        info.user_name = "test"
        info.server_version = "test"
        info.host_name = "test"
        self.pulse.server_info.return_value = info

        response = self.api.get_info(request)
        data = json.loads(response)
        assert data['default_sink_name'] == "test"

    def test_update_info(self):
        request = MagicMock()

        data = {
            'default_sink_name': 'test',
            'default_source_name': 'test'
        }
        request.content.read.return_value = json.dumps(data)

        response = self.api.update_info(request)
        data = json.loads(response)
        assert data['default_sink_name'] == 'test'
        assert data['default_source_name'] == 'test'

    def test_get_modules(self):
        request = MagicMock()

        module = MagicMock()
        module.index = 0
        module.name = "test"
        module.n_used = 0
        self.pulse.module_list.return_value = [module]

        response = self.api.get_modules(request)
        data = json.loads(response)
        assert len(data) == 1
        assert data[0]['name'] == "test"

    def test_load_module(self):
        request = MagicMock()

        data = { 'name': 'module-test' }
        request.content.read.return_value = json.dumps(data)

        self.pulse.module_load.return_value = 42

        response = self.api.load_module(request)
        data = json.loads(response)
        assert data['index'] == 42

    def test_get_sinks(self):
        request = MagicMock()

        sink = MagicMock()
        sink.channel_count = 2
        sink.channel_list = ["front-left", "front-right"]
        sink.description = "test"
        sink.index = 0
        sink.name = "test"
        sink.volume = MagicMock()
        sink.volume.values = [1.0, 1.0]
        self.pulse.sink_list.return_value = [sink]

        response = self.api.get_sinks(request)
        data = json.loads(response)
        assert len(data) == 1
        assert data[0]['name'] == "test"

    def test_set_sink_volume(self):
        request = MagicMock()

        data = [1.0, 1.0]
        request.content.read.return_value = json.dumps(data)

        # This sink does not exist.
        response = self.api.set_sink_volume(request, "not-found")
        assert response == "{}"

        sink = MagicMock()
        sink.name = "test"
        self.pulse.sink_list.return_value = [sink]

        # This sink exists, so setting the volume should succeed.
        response = self.api.set_sink_volume(request, "test")
        assert response != "{}"

    def test_get_sources(self):
        request = MagicMock()

        source = MagicMock()
        source.channel_count = 2
        source.channel_list = ["front-left", "front-right"]
        source.description = "test"
        source.index = 0
        source.name = "test"
        source.volume = MagicMock()
        source.volume.values = [1.0, 1.0]
        self.pulse.source_list.return_value = [source]

        response = self.api.get_sources(request)
        data = json.loads(response)
        assert len(data) == 1
        assert data[0]['name'] == "test"

    def test_set_source_volume(self):
        request = MagicMock()

        data = [1.0, 1.0]
        request.content.read.return_value = json.dumps(data)

        # This source does not exist.
        response = self.api.set_source_volume(request, "not-found")
        assert response == "{}"

        source = MagicMock()
        source.name = "test"
        self.pulse.source_list.return_value = [source]

        # This source exists, so setting the volume should succeed.
        response = self.api.set_source_volume(request, "test")
        assert response != "{}"
