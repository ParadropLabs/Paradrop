'''
Storage and stateful functionality for pdfcd. 
'''

import os
import yaml

from paradrop.lib import settings


class Store(object):

    def __init__(self):

        # Create our persistence directory
        if not os.path.exists(settings.STORE_PATH):
            os.makedirs(settings.STORE_PATH)

        # No config file found. Create a default one
        if not os.path.isfile(settings.INFO_PATH):
            createDefault()

        with open(settings.INFO_PATH, 'r') as f:
            self.baseConfig = yaml.load(f)


def createDefault():
    default = '''
    version: 1
    accounts: ""
    currentAccount: null
    '''

    writeYaml(default, INFO_PATH)


def writeYaml(contents, path):
    ''' Overwrites content '''
    with open(path, 'w') as f:
        f.write(yaml.dump(contents, default_flow_style=False))
