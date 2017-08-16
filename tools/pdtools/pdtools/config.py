import os

import appdirs
import yaml


class PdtoolsConfig(object):
    def __init__(self, data=None):
        if data is not None:
            self.data = data
        else:
            self.data = {}

    def addControllerToken(self, host, username, token):
        """
        Add a new auth token for a controller.
        """
        if 'controllers' not in self.data:
            self.data['controllers'] = []

        self.data['controllers'].append({
            'host': host,
            'token': token,
            'username': username
        })

    def getControllerToken(self, host):
        """
        Get a saved auth token for a controller.
        """
        for ctrl in self.data.get('controllers', []):
            if ctrl['host'] == host:
                return ctrl.get('token', None)
        return None

    def removeControllerToken(self, token):
        """
        Remove a saved auth token for a controller.
        """
        old = self.data.get('controllers', [])
        self.data['controllers'] = [x for x in old if not x['token'] == token]

    def save(self):
        """
        Save the configuration file.
        """
        config_dir = appdirs.user_config_dir('pdtools', 'paradrop')
        path = os.path.join(config_dir, 'config.yaml')

        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        with open(path, 'w') as output:
            yaml.safe_dump(self.data, output, default_flow_style=False)

    @classmethod
    def load(cls):
        """
        Load the configuration file.

        Returns an empty PdconfConfig object if the file could not be read.
        """
        config_dir = appdirs.user_config_dir('pdtools', 'paradrop')
        path = os.path.join(config_dir, 'config.yaml')

        try:
            with open(path, 'r') as source:
                config = yaml.safe_load(source)
                return cls(config)
        except:
            return cls()
