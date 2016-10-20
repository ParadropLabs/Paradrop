import json
import time

import requests


class ProgressHandler(object):
    def __init__(self, authorization=None, **kwargs):
        self.completed_url = "{}/api/routers/{}/updates/{}".format(
            kwargs.get('server', 'https://paradrop.org'),
            kwargs.get('router_id', 0),
            kwargs.get('update_id', 0))
        self.message_url = "{}/api/routers/{}/updates/{}/messages".format(
            kwargs.get('server', 'https://paradrop.org'),
            kwargs.get('router_id', 0),
            kwargs.get('update_id', 0))

        self.session = requests.Session()
        self.session.headers.update({'content-type': 'application/json'})
        if authorization is not None:
            self.session.headers.update({'authorization': authorization})

    def complete(self, success=False):
        data = [
            {'op': 'replace', 'path': '/completed', 'value': True},
            {'op': 'replace', 'path': '/success', 'value': success}
        ]
        response = self.session.patch(self.completed_url, json.dumps(data), stream=False)

    def write(self, message):
        data = {
            'time': time.time(),
            'message': message
        }
        response = self.session.post(self.message_url, json.dumps(data), stream=False)
