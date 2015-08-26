'''
Storage and stateful functionality for tools and paradrop. 

Holds onto the following things:
    Keys
    Identity
    Logs 
        Not really, Twisted is handling this-- we just make the directory here
'''

import os
import yaml

from os.path import expanduser
from pdtools.lib.output import out

# Check and see if we're on snappy or not. If not, then stick the logs in the local
# directory. We will be provisioned as a developer instance anyway, so the info doesn't matter yet,
# Also doesn't really matter for the buildtools, although it is a bit of a vulnurability
snappyPath = os.getenv("SNAP_APP_DATA_PATH", None)

STORE_PATH = snappyPath + '/' if snappyPath is not None else expanduser('~') + '/.paradrop/'

LOG_PATH = STORE_PATH + 'logs/'
KEY_PATH = STORE_PATH + 'keys/'
MISC_PATH = STORE_PATH + 'misc/'
INFO_PATH = STORE_PATH + 'root.yaml'

# Keys required in the store
INFO_REQUIRES = ['version', 'pdid', 'chutes', 'routers', 'instances']


class Storage(object):

    def __init__(self, autoSave=True, router=False):
        '''
        Autosave saves baseConfig on change. (not implemented, see methods below)

        The router optional flag should be set to configure runtime store allocation specific 
        for VM routers
        '''
        self.autosave = autoSave

        # Check and see if we are running locally-- if so place the logs in a subdirectory
        # and respecify the paths
        if router:
            configureLocalPaths()

        # Create needed directories
        for path in [STORE_PATH, KEY_PATH, LOG_PATH, MISC_PATH]:
            if not os.path.exists(path):
                os.makedirs(path)

        # No config file found. Create a default one
        if not os.path.isfile(INFO_PATH):
            createDefaultInfo(INFO_PATH)

        self.baseConfig = loadYaml(INFO_PATH)

        # Sanity check contents of info and throw it out if bad
        if not validateInfo(self.baseConfig):
            out.warn('Saved configuration data invalid, destroying it.')
            os.remove(INFO_PATH)
            createDefaultInfo(INFO_PATH)
            self.baseConfig = loadYaml(INFO_PATH)

    def close(self):
        ''' Close and write out. This is automatic if autoSave is on'''
        pass

    def saveConfig(self, key, value):
        self.baseConfig[key] = value

        if self.autosave:
            writeYaml(self.baseConfig, INFO_PATH)

    def getConfig(self, key):
        return self.baseConfig[key]

    def saveKey(self, key, name):
        ''' Save the key with the given name. Overwrites by default '''
        path = KEY_PATH + name

        # Overwrite existing keys when asked for now
        # if os.path.isfile(path):
        #     print 'Key already exists!'
        #     pass

        with open(path, 'wb') as f:
            f.write(key)

    def getKey(self, name):
        ''' Returns the given key or None '''
        path = KEY_PATH + name

        if os.path.isfile(path):
            with open(path, 'rb') as f:
                return f.read()

        return None

    def saveMisc(self, contents, name):
        pass

    def loggedIn(self):
        ''' 
        Robustly determine if the account stored is logged in

        NOTE: not complete
        '''

        # currently just check for presence of saved id field
        return True if self.baseConfig['pdid'] else False


def configureLocalPaths():
    ''' Alter paths if the router is running as a vm '''
    global STORE_PATH, LOG_PATH, KEY_PATH, MISC_PATH, INFO_PATH

    # If not on snappy, we're a router running locally
    if not snappyPath:
        STORE_PATH = expanduser('~') + '/.paradrop/local/'

        LOG_PATH = STORE_PATH + 'logs/'
        KEY_PATH = STORE_PATH + 'keys/'
        MISC_PATH = STORE_PATH + 'misc/'
        INFO_PATH = STORE_PATH + 'root.yaml'


def validateInfo(contents):
    '''
    Error checking on the read YAML file. 

    :param contents: the read-in yaml to check
    :type contents: dict.
    :returns: True if valid, else false
    '''
    for k in INFO_REQUIRES:
        if k not in contents:
            return False

    # Check the validity of the contents

    return True


def createDefaultInfo(path):
    default = {
        'version': 1,
        'pdid': "",
        'chutes': [],
        'routers': [],
        'instances': []
    }

    writeYaml(default, path)


def writeYaml(contents, path):
    ''' Overwrites content with YAML representation at given path '''
    with open(path, 'w') as f:
        f.write(yaml.dump(contents, default_flow_style=False))


def loadYaml(path):
    ''' Return dict from YAML found at path '''
    with open(path, 'r') as f:
        return yaml.load(f.read())


# Global singleton (lite). This is NOT set up by default (else testing would be a
# nightmare.) The main script should set this up when ready to rock
store = Storage()
