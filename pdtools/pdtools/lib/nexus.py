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
import json

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
        self.paths = AttrWrapper()
        self.net = AttrWrapper()
        self.meta = AttrWrapper()
        self.info = AttrWrapper()

        # Replace settings values with environment variables

        # Set meta
        self.meta.type = nexusType
        self.meta.mode = mode
        self.meta.version = NexusBase.VERSION

        # Set paths
        makePaths(self)

        # Set network
        resolveNetwork(self, self.meta.mode)

        # Set info by loading from paths
        loadConfig(self, self.paths.config)

        # Lock all the wrapper objects except info. That one we register to the save function
        [x._lock() for x in [self.paths, self.net, self.meta]]
        self.info.setOnChange(self.onInfoChange)

        # Done with data initizlization. From here on out its configuration and state

        # initialize output. If filepath is set, logs to file.
        # If stealStdio is set intercepts all stderr and stdout and interprets it internally
        # If printToConsole is set (defaults True) all final output is rendered to stdout
        # output.out.startLogging(filePath=self.logPath, stealStdio=stealStdio, printToConsole=printToConsole)

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

    def onInfoChange(self, key, value):
        '''
        Called when an internal setting is changed. Trigger a save automatically.
        '''
        self.save()

    def save(self):
        ''' Ehh. Ideally this should happen asynchronously. '''
        writeYaml(self.info.__dict__['contents'], self.paths.config)

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
    # Misc
    #########################################################

    def __repr__(self):
        ''' Dump everything '''
        dic = dict(paths=self.paths.contents,net=self.net.contents, info=self.info.contents, meta=str(self.meta))
        return json.dumps(dic, sort_keys=True, indent=4)

#########################################################
# Utils
#########################################################


class AttrWrapper(object):

    '''
    Simple attr interceptor to make accessing settings simple and magical. 
    Because we all could use a little magic in our day. 

    Stores values in an internal dict called contents. 

    Does not allow modification once _lock() is called. Respect it.

    Once you've filled it up with the appropriate initial values, set
    onChange to assign 
    '''

    def __init__(self):
        self.__dict__['contents'] = {}

        # Called when a value changes unless None
        self.__dict__['onChange'] = None

        # Lock the contents of this wrapper. Can read valued, cant write them
        self.__dict__['locked'] = False

    def _lock(self):
        self.__dict__['locked'] = True

    def setOnChange(self, func):
        assert(callable(func))
        self.__dict__['onChange'] = func

    def __repr__(self):
        return str(self.contents)

    def __getattr__(self, name):
        return self.__dict__['contents'][name]

    def __setattr__(self, k, v):
        if self.__dict__['locked']:
            raise AttributeError('This attribute wrapper is locked. You cannot change its values.')

        self.contents[k] = v

        if self.__dict__['onChange'] is not None:
            self.__dict__['onChange'](k, v)


def resolveNetwork(nexus, mode):
    ''' Given a nexus object and its mode, set its network values '''
    nexus.net.webPort = eval('NexusBase.PORT_HTTP_%s' % mode.name.upper())
    nexus.net.port = eval('NexusBase.PORT_WS_%s' % mode.name.upper())

    nexus.net.webHost = eval('NexusBase.HOST_HTTP_%s' % mode.name.upper())
    nexus.net.host = eval('NexusBase.HOST_WS_%s' % mode.name.upper())

    # Interpolating the websockets port into the url
    nexus.net.host = nexus.net.host.replace('PORT', nexus.net.port)
    


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


def loadConfig(nexus, path):
    '''
    Given a path to the config file, load its contents and assign it to the 
    config file as appropriate. 
    '''

    # Check to make sure we have a default settings file
    if not os.path.isfile(path):
        createDefaultInfo(path)

    contents = loadYaml(path)

    # Sanity check contents of info and throw it out if bad
    if not validateInfo(contents):
        output.out.err('Saved configuration data invalid, destroying it.')
        os.remove(path)
        createDefaultInfo(path)
        contents = loadYaml(path)

    nexus.info.pdid = contents['pdid']
    # nexus.info.owner = contents['version']


def createDefaultInfo(path):
    default = {
        'version': 1,
        'pdid': None
    }

    writeYaml(default, path)


def validateInfo(contents):
    '''
    Error checking on the read YAML file. This is a temporary method.

    :param contents: the read-in yaml to check
    :type contents: dict.
    :returns: True if valid, else false
    '''
    INFO_REQUIRES = ['version', 'pdid']

    for k in INFO_REQUIRES:
        if k not in contents:
            return False

    return True


def writeYaml(contents, path):
    ''' Overwrites content with YAML representation at given path '''
    with open(path, 'w') as f:
        f.write(yaml.dump(contents, default_flow_style=False))


def loadYaml(path):
    ''' Return dict from YAML found at path '''
    with open(path, 'r') as f:
        return yaml.load(f.read())
