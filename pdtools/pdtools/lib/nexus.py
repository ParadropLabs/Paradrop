'''
Stateful, singleton, command and control center. This is the brains of the three 
paradrop components: tools, router, and server.

Takes over the functionality of the following modules, globals, and all around cruft:
    settings
    storage (keys, settings, names, permissions)
    chuteStore
    port/host consts
    portal and server administration

Additionally:
    Persists data to disk synchronously (for now, unless it gets hairy.)
    Manages init and deinit
    Document versioning, migrations, and validations through barit.

This object is meant to be subclassed by each of the three PD components. 
They should build upon the methods below as it suits their needs-- for example, 
tools may need to store information about routers, routers will store 
chutes, and the server will rely heavily on riffle callbacks.

Should make this a singleton. And make a print thread for this guy, just for safety.

The base class does not implement any riffle integration other than 
setting up the keys and default connection information. You should register for 
connection callbacks using smokesignals (see paradrop/main.py). DO NOT
store connections yourself-- riffle already does that and you'll screw up the portal!

Version 2 changes: 
    Should be able to call nexus.core.paths.logPath
'''

import os
import yaml

from enum import Enum
import smokesignal
from twisted.internet import reactor

from pdtools.lib import store, riffle, output

# Global access. Assign this wherever you instantiate the Nexus object:
#       nexus.core = MyNexusSubclass()
core = None

# The type and mode of this nexus instance
Type = Enum('Type', 'router, tools, server')
Mode = Enum('Mode', 'production, development, test, local')


class NexusBase(object):

    '''
    These are the boilerplate, initial settings values. 

    DO NOT MODIFY THESE AT RUNTIME. Instead, query the nexus object for 
    the appropriate attribute. These are here for two purposes: declare
    which settings will be present in the nexus object, and show you their names.

    There are three steps that take place in resolving these valus to their 
    final forms:
        1- this module is imported, initial values assigned (as written below)
        2- this class is instatiated, reading in environment variables and replacing 
            any those it finds
        3- runtime level modification of settings as appropriate

    Note the last step. Some variables simply cannot be changed. 

    Not implemented: settings, chutes
    '''

    ###############################################################################
    # Paths. Dump: 'print nexus.core.paths'
    ###############################################################################

    # The three options for root file directory. Eventually end up in nexus.core.paths.root
    PATH_ROOT = None                                    # nexus.core.paths.root
    PATH_SNAPPY = os.getenv("SNAP_APP_DATA_PATH", None)
    PATH_LOCAL = os.path.expanduser('~') + '/.paradrop/local/'
    PATH_HOME = os.path.expanduser('~') + '/.paradrop/'
    PATH_CURRENT = os.getcwd() + '/.paradrop/'

    PATH_LOG = '/logs/'                                 # nexus.core.paths.log
    PATH_KEY = '/keys/'                                 # nexus.core.paths.key
    PATH_MISC = '/misc/'                                # nexus.core.paths.misc
    PATH_CONFIG = '/config'                             # nexus.core.paths.config

    ###############################################################################
    # Net. Dump: 'print nexus.core.net'
    ###############################################################################

    # Note: one of the options are picked  based on the mode
    HOST_HTTP_PRODUCTION = 'https://paradrop.io'        # nexus.core.net.webHost
    HOST_HTTP_DEVELOPMENT = 'https://paradrop.io'
    HOST_HTTP_TEST = 'localhost'
    HOST_HTTP_LOCAL = 'localhost'

    PORT_HTTP_PRODUCTION = '14321'                      # nexus.core.net.webPort
    PORT_HTTP_DEVELOPMENT = '14321'
    PORT_HTTP_TEST = '14321'
    PORT_HTTP_LOCAL = '14321'

    # Web Sockets host and port
    HOST_WS_PRODUCTION = 'ws://paradrop.io:PORT/ws'     # nexus.core.net.host
    HOST_WS_DEVELOPMENT = "ws://paradrop.io:PORT/ws"
    HOST_WS_TEST = "ws://127.0.0.1:PORT/ws"
    HOST_WS_LOCAL = "ws://127.0.0.1:PORT/ws"

    PORT_WS_PRODUCTION = '9080'                         # nexus.core.net.port
    PORT_WS_DEVELOPMENT = '9080'
    PORT_WS_TEST = '9080'
    PORT_WS_DEVELOPMENT = '9080'

    ###############################################################################
    # Meta. Dump: 'print nexus.core.meta'
    ###############################################################################

    # One of the enum values above this class. Note: the value here is *not*
    # applied to the nexus object (except for version) since they are received
    # as direct parameters to the initialization method. You can still set
    # environment variables that match these names, they will overwrite the final values
    TYPE = None                                         # nexus.core.meta.type
    MODE = None                                         # nexus.core.meta.mode
    VERSION = 1                                         # nexus.core.meta.version

    ###############################################################################
    # Info. Dump: 'print nexus.core.info'
    ###############################################################################

    # One of the enum values above this class
    PDID = None                                         # nexus.core.info.pdid
    OWNER = None                                        # nexus.core.info.owner

    def __init__(self, nexusType, mode=Mode.development, stealStdio=True, printToConsole=True):
        '''
        The one big thing this function leaves out is reactor.start(). Call this externally 
        *after* initializing a nexus object. 

        :param type: one of [router, tool, server]
        :type type: str.
        :param mode: one of [production, development, test, local]. Changes host and ports.
            See section "network resolution" below 
        '''

        # Create the attr redirectors. These allow for nexus.net.stuff
        self.paths = AttrRedirect()
        self.net = AttrRedirect()
        self.meta = AttrRedirect()
        self.info = AttrRedirect()

        # Set meta
        self.meta.type = nexusType
        self.meta.mode = mode
        self.meta.version = NexusBase.VERSION

        # Set paths
        makePaths(self)

        # Set network
        resolveNetwork(self, self.meta.mode)

        # Set info by loading from paths
        # self.load()

        # initialize output. If filepath is set, logs to file.
        # If stealStdio is set intercepts all stderr and stdout and interprets it internally
        # If printToConsole is set (defaults True) all final output is rendered to stdout
        # output.out.startLogging(filePath=self.logPath, stealStdio=stealStdio, printToConsole=printToConsole)

        # Asssign global riffle keys
        # riffle.portal.keyPrivate = self.getKey('pub')
        # riffle.portal.certCa = self.getKey('ca')
        # riffle.portal.host = self.serverHost()
        # riffle.portal.port = self.rifflePort()

        # register onStop for the shutdown call
        # reactor.addSystemEventTrigger('before', 'shutdown', self.onStop)
        # reactor.callLater(0, self.onStart)

    def onStart(self):
        pdid = self.get('pdid') if self.provisioned() else 'unprovisioned router'

        output.out.usage('%s (%s) coming up' % (pdid, self.type))

    def onStop(self):
        self.save()

        # riffle.portal.close()

        # remove any and all pubsub registrations. If not done, this can cause
        # issues with subs that have to do with network connections

        output.out.usage('%s going down' % self.type)
        smokesignal.clear_all()
        output.out.endLogging()

<< << << < Updated upstream
    def makePaths(self):
        '''
        Are we on a VM? On snappy? Bare metal? The server?  So many paths, so few answers!
        '''

        # Lets start out being a router
        self.rootPath = os.getenv("SNAP_APP_USER_DATA_PATH", None)

        # Put tools contents in the home directory
        if self.type is 'tool':
            self.rootPath = os.path.expanduser('~') + '/.paradrop/'

        # Current directory (since we might have more than one server at a time)
        elif self.type is 'server':
            self.rootPath = os.getcwd() + '/.paradrop/'

        # We're a router, yay! But are we a router on snappy or local? The snappy
        # path will not resolve on a local machine-- let it fall through, we're set
        elif not self.rootPath:
            self.rootPath = os.path.expanduser('~') + '/.paradrop/local/'

        # Set the boring paths
        self.logPath = self.rootPath + '/logs/'
        self.keyPath = self.rootPath + '/keys/'
        self.miscPath = self.rootPath + '/misc/'
        self.configPath = self.rootPath + '/config'  # this is a path, not a file

        # create the paths
        for x in [self.rootPath, self.logPath, self.keyPath, self.miscPath]:
            if not os.path.exists(x):
                os.makedirs(x)

== == == =
>>>>>> > Stashed changes
    def load(self):
        '''
        Load our settings/configuration data from the path ivars. Does not check if the paths are None.

        This is a combo of functionality from store and settings. The method of loading is configurable. 
        Right now its YAML.
        '''

        # Check to make sure we have a default settings file
        if not os.path.isfile(self.configPath):
            createDefaultInfo(self.configPath)

        self.config = loadYaml(self.configPath)

        # Sanity check contents of info and throw it out if bad
        if not validateInfo(self.config):
            out.err('Saved configuration data invalid, destroying it.')
            os.remove(self.configPath)
            createDefaultInfo(self.configPath)
            self.config = loadYaml(self.configPath)

    def save(self):
        ''' Ehh. Ideally this should happen constantly and asynchronously. '''
        writeYaml(self.config, self.configPath)

    #########################################################
    # Settings
    #########################################################

    def set(self, k, v):
        self.config[k] = v
        self.save()

    def get(self, k):
        return self.config[k]

    def provisioned(self):
        return self.config['pdid'] is not None

    #########################################################
    # Keys
    #########################################################

    def saveKey(self, key, name):
        ''' Save the key with the given name. Overwrites by default '''
        path = self.keyPath + name

        with open(path, 'wb') as f:
            f.write(key)

    def getKey(self, name):
        ''' Returns the given key or None '''
        path = self.keyPath + name

        if os.path.isfile(path):
            with open(path, 'rb') as f:
                return f.read()

        return None

    #########################################################
    # Chutes
    #########################################################

    def chute(self, name):
        return None

    def chutes(self):
        return []

    def removeChute(self, name):
        pass

    def addChute(self, name):
        pass

    #########################################################
    # Network Resolution
    #########################################################

    def serverHost(self):
        ''' Different in production vs dev, etc. Returns hostname '''
        if self.mode == 'local':
            return 'localhost'

        return 'paradrop.io'

    def rifflePort(self):
        return _incrementingPort(8016, self.mode)

    def insecureRifflePort(self):
        ''' This isnt a thing yet. But it will be. '''
        return _incrementingPort(8017, self.mode)

    def webPort(self):
        return _incrementingPort(14321, self.mode)

    #########################################################
    # Path Resolution
    #########################################################

    def logPath(self):
        return self.logPath

    def keyPath(self):
        return self.keyPath

    def chutePath(self):
        return self.chutePath

    def uciPath(self):
        pass


#########################################################
# Utils
#########################################################

class AttrRedirect(object):

    '''
    Simple attr interceptor to make accessing settings simple and magical. 
    Because we all could use a little magic in our day. 
    '''

    def __init__(self):
        self.__dict__['contents'] = {}

    def __repr__(self):
        return str(self.contents)

    def __getattr__(self, name):
        return self.__dict__['contents'][name]

    def __setattr__(self, k, v):
        self.contents[k] = v


def _incrementingPort(base, mode):
    ''' Returns the given port plus some multiple of 10000 based on the passed mode '''

    if mode == 'production' or mode == 'local':
        return base

    if mode == 'development':
        return base + 10000

    if mode == 'test':
        return base + 10000 * 2

    return base


def resolveNetwork(nexus, mode):
    ''' Given a nexus object and its mode, set its network values '''
    nexus.net.webHost = eval('NexusBase.HOST_HTTP_%s' % mode.name.upper())
    nexus.net.webPort = eval('NexusBase.PORT_HTTP_%s' % mode.name.upper())
    nexus.net.host = eval('NexusBase.HOST_WS_%s' % mode.name.upper())
    nexus.net.port = eval('NexusBase.HOST_WS_%s' % mode.name.upper())


def makePaths(nexus):
    '''
    Are we on a VM? On snappy? Bare metal? The server?  So many paths, so few answers!
    '''

    # Default use the Home path (covers tools)
    nexus.paths.root = NexusBase.PATH_HOME

    # Always use current directory when server (since there could be more than one of them )
    if nexus.meta.type == Type.server:
        nexus.paths.root = NexusBase.PATH_CURRENT

    # we can either resolve the root path based on the mode (which
    # is prefereable) or continue to just use the snappy check to set it
    # In other words, path_snappy if in snappy, else path_vm
    if nexus.meta.type == Type.router:
        if nexus.PATH_SNAPPY is None:
            nexus.paths.root = NexusBase.PATH_LOCAL
        else:
            nexus.paths.root = NexusBase.PATH_SNAPPY

    # Set boring paths
    nexus.paths.log = nexus.paths.root + NexusBase.PATH_LOG
    nexus.paths.key = nexus.paths.root + NexusBase.PATH_KEY
    nexus.paths.misc = nexus.paths.root + NexusBase.PATH_MISC
    nexus.paths.config = nexus.paths.root + NexusBase.PATH_CONFIG

    # create the paths
    for x in [nexus.paths.root, nexus.paths.log, nexus.paths.key, nexus.paths.misc]:
        if not os.path.exists(x):
            os.makedirs(x)


def createDefaultInfo(path):
    default = {
        'version': 1,
        'pdid': None,
        'chutes': [],
        'routers': [],
        'instances': []
    }

    writeYaml(default, path)


def validateInfo(contents):
    '''
    Error checking on the read YAML file. This is a temporary method.

    :param contents: the read-in yaml to check
    :type contents: dict.
    :returns: True if valid, else false
    '''
    INFO_REQUIRES = ['version', 'pdid', 'chutes', 'routers', 'instances']

    for k in INFO_REQUIRES:
        if k not in contents:
            return False

    # Check the validity of the contents

    return True


def writeYaml(contents, path):
    ''' Overwrites content with YAML representation at given path '''
    with open(path, 'w') as f:
        f.write(yaml.dump(contents, default_flow_style=False))


def loadYaml(path):
    ''' Return dict from YAML found at path '''
    with open(path, 'r') as f:
        return yaml.load(f.read())
