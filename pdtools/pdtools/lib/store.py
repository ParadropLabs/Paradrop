'''
Simple storage.

Creates directories in home folder for storage. Each account that logs in gets 
a YAML file for their settings. Current logged in user gets an auth key.

Root settings are held in a main.yaml file.
'''

import os
import yaml

PATH = '~/.paradrop/'
ROOT = 'root.yaml'


class Store(object):

    def __init__(self):
        if not os.path.exists(PATH):
            os.makedirs(PATH)

        # No config file found. Create a default one
        if not os.path.isfile(PATH + ROOT):
            createDefault()

        with open(PATH + ROOT, 'r') as f:
            self.baseConfig = yaml.load(f)


def createDefault():
    default = '''
    version: 1
    accounts: ""
    currentAccount: null
    '''

    writeYaml(default, PATH + ROOT)


def writeYaml(contents, path):
    ''' Overwrites content '''
    with open(path, 'w') as f:
        f.write(yaml.dump(contents, default_flow_style=False))
