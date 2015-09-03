'''
Stateful, singleton, command and control center. This is the brains of the three
paradrop components: tools, router, and server.

See docstring for NexusBase class for information on settings.

SETTINGS QUICK REFERENCE:
    # assuming the following import
    from pdtools.lib import nexus

    nexus.core.path.root
    nexus.core.path.log
    nexus.core.path.key
    nexus.core.path.misc
    nexus.core.path.config

    nexus.core.net.webHost
    nexus.core.net.webPort
    nexus.core.net.host
    nexus.core.net.port

    nexus.core.meta.type
    nexus.core.meta.mode
    nexus.core.meta.version

    nexus.core.info.pdid
'''

import os
import yaml
import json

from enum import Enum
import smokesignal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

from pdtools.lib import output, cxbr

# Global access. Assign this wherever you instantiate the Nexus object:
#       nexus.core = MyNexusSubclass()
core = None

# The type and mode of this nexus instance
Type = Enum('Type', 'router, tools, server')
Mode = Enum('Mode', 'production, development, test, local')


class NexusBase(object):

    '''
    Initial settings values.

    Resolving these values to their final forms:
        1 - module imported, initial values assigned(as written below)
        2 - class is instatiated, passed settings or environ replace values
        3 - instance chooses appropriate values based on current state(production, router, etc)
            Each category has its own method for initialization here
            (see: resolveNetwork, resolvePaths)

    DO NOT MODIFY CONSTS AT RUNTIME. Add new settings, pass in settings changes,
    or set environment variables.

    DO NOT ACCESS CONSTS AT RUNTIME. These are the initial states. They are
    evaluated and mapped to readable names. Their resulting attribute names are
    shown as a comment to the right of each declaration.

    To dump all values:
        from pdtools.lib import nexus
        print nexus.core

    To dump a subset of values:
        from pdtools.lib import nexus
        print nexus.core.net
        print nexus.core.path

    Not yet implemented:
        settings, chutes

    EXAMPLE:
        We want to resolve port dynamically based on type and mode. First,
        we enumerate the possibilities as consts:
            PORT_PRODUCTION = 1234                          # nexus.core.net.port
            PORT_DEVELOPMENT = 2345

        (The right - justified comment indicates where the final value resides)

        To change the const at runtime, instantiate the object with settings override:
            NexusBase(Type.router, Mode.production, settings=['PORT_PRODUCTION:3456'])

        Or set an environment variable before running:
            export PORT_PRODUCTION = 3456

        When instantiating, class checks for mode in "resolveNetwork"
            if nex.meta.type == Type.Production:
                nex.net.port = PORT_PRODUCTION

            (magic omitted)

        Finally access the resulting values:
            from pdtools.lib import nexus
            print nexus.core.net.port
            = > '3456'

    '''

    ###############################################################################
    # Paths. Dump: 'print nexus.core.path'
    ###############################################################################

    PATH_SNAPPY = os.getenv("SNAP_APP_DATA_PATH", None)
    PATH_LOCAL = os.path.expanduser('~') + '/.paradrop/local'
    PATH_HOME = os.path.expanduser('~') + '/.paradrop'
    PATH_CURRENT = os.getcwd() + '/.paradrop'
    PATH_ROOT = None                                   # nexus.core.path.root

    PATH_LOG = 'logs/'                                 # nexus.core.path.log
    PATH_KEY = 'keys/'                                 # nexus.core.path.key
    PATH_MISC = 'misc/'                                # nexus.core.path.misc
    PATH_CONFIG = 'config'                             # nexus.core.path.config

    # This needs work
    PDCONFD_WRITE_DIR = '/var/run/pdconfd'             # nexus.core.path.pdconfdWrite
    PDCONFD_WRITE_DIR_LOCAL = "/tmp/pdconfd"

    UCI_CONFIG_DIR = "/etc/config"                     # nexus.core.path.uciConfig
    UCI_CONFIG_DIR_SNAPPY = "config.d"
    UCI_CONFIG_DIR_LOCAL = "/tmp/config.d"

    HOST_CONFIG_PATH = "/etc/paradrop_host_config"     # nexus.core.path.hostConfig
    HOST_CONFIG_PATH_LOCAL = "/tmp/hostconfig.yaml"

    DOCKER_BIN_DIR = "/apps/bin"                       # nexus.core.path.docker

    ###############################################################################
    # Network.
    # Dump: 'print nexus.core.net'
    ###############################################################################

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
    PORT_WS_LOCAL = '9080'

    ###############################################################################
    # Meta. Values that tell you something about the values in here
    # Dump: 'print nexus.core.meta'
    ###############################################################################

    TYPE = None                                         # nexus.core.meta.type
    MODE = None                                         # nexus.core.meta.mode
    VERSION = 1                                         # nexus.core.meta.version

    ###############################################################################
    # Configuration. Affect the whole system, generally static
    # Dump: 'print nexus.core.conf'
    ###############################################################################

    DYNAMIC_NETWORK_POOL = "192.168.128.0/17"           # nexus.core.conf.networkPool
    PDCONFD_ENABLED = True                              # nexus.core.conf.pdconfdEnabled
    FC_BOUNCE_UPDATE = None                             # nexus.core.conf.fcBounceUpdate
    RESERVED_CHUTE = "__PARADROP__"                     # nexus.core.conf.reservedChute
    FC_CHUTESTORAGE_SAVE_TIMER = 60                     # nexus.core.conf.chuteSaveTimer

    ###############################################################################
    # Info. Values that are likely to change with individual users.
    # Dump: 'print nexus.core.info'
    ###############################################################################

    # One of the enum values above this class
    PDID = None                                         # nexus.core.info.pdid

    def __init__(self, nexusType, mode=Mode.development, settings=[], stealStdio=True, printToConsole=True):
        '''
        The one big thing this function leaves out is reactor.start(). Call this externally
        *after * initializing a nexus object.
        '''

        # Create the attr redirectors. These allow for nexus.net.stuff
        self.path = AttrWrapper()
        self.net = AttrWrapper()
        self.meta = AttrWrapper()
        self.conf = AttrWrapper()
        self.info = AttrWrapper()

        # Replace values with settings or environ vars
        overrideSettingsList(self.__class__, settings)
        overrideSettingsEnv(self.__class__)

        # Resolve all the final attribute values
        resolveMeta(self, nexusType, mode)
        resolvePaths(self)
        resolveNetwork(self, self.meta.mode)
        resolveConfig(self, self.meta.mode)
        resolveInfo(self, self.path.config)

        # Lock all the wrapper objects except info. That one we register to the save function
        # Paths, network, etc, cannot be changed from here on out to discourage unsafe usage
        [x._lock() for x in [self.path, self.net, self.meta]]
        self.info.setOnChange(self.onInfoChange)

        # initialize output. If filepath is set, logs to file.
        # If stealStdio is set intercepts all stderr and stdout and interprets it internally
        # If printToConsole is set (defaults True) all final output is rendered to stdout
        output.out.startLogging(filePath=self.path.log, stealStdio=stealStdio, printToConsole=printToConsole)

        # register onStop for the shutdown call
        reactor.addSystemEventTrigger('before', 'shutdown', self.onStop)

        # The reactor needs to be runnnig before this call is fired, since we start the session
        # here. Assuming callLater doesn't fire until thats happened
        reactor.callLater(0, self.onStart)

    def onStart(self):
        pdid = self.info.pdid if self.provisioned() else 'UNPROVISIONED'
        output.out.usage('%s (%s: %s) coming up' % (self.info.pdid, self.meta.type, self.meta.mode))

        # Start trying to connect to cxbr fabric

    def onStop(self):
        self.save()

        output.out.usage('%s (%s) going down' % (self.info.pdid, self.meta.type))
        smokesignal.clear_all()
        output.out.endLogging()

    @inlineCallbacks
    def connect(self, sessionClass, debug=False):
        '''
        Takes the given session class and attempts to connect to the crossbar fabric.

        If an existing session is connected, it is cleanly closed.
        '''

        print 'Connecting to node at URI: ' + str(self.net.host)
        self.session = yield sessionClass.start(self.net.host, self.info.pdid, debug=debug)
        returnValue(self.session)

    def onConnect(self):
        '''
        Called when the session passed into connect suceeds in its connection.
        That session object is assigned to self.session.
        '''
        if not self.provisioned():
            output.out.warn('Router has no keys or identity. Waiting to connect to to server.')
        else:
            reactor.callLater(.1, self.connect)

    def onDisconnect(self):
        ''' Called when the crossbar session disconnects intentionally (cleanly). '''
        pass

    def onConnectionLost(self):
        ''' Called when our session is lost by accident. '''
        pass

    def onInfoChange(self, key, value):
        '''
        Called when an internal setting is changed. Trigger a save automatically.
        '''
        self.save()

    def save(self):
        ''' Ehh. Ideally this should happen asynchronously. '''
        saveDict = self.info.__dict__['contents']
        saveDict['version'] = self.meta.version

        writeYaml(saveDict, self.path.config)

    #########################################################
    # High Level Methods
    #########################################################

    def provisioned(self):
        '''
        Checks if this[whatever] appears to be provisioned or not
        '''

        return self.info.pdid is not None

    def provision(self, pdid, keys):
        ''' Temporary method, things dont work like this anymore '''

        self.info.pdid = pdid

    #########################################################
    # Keys
    #########################################################

    def saveKey(self, key, name):
        ''' Save the key with the given name. Overwrites by default '''
        path = self.path.key + name

        with open(path, 'wb') as f:
            f.write(key)

    def getKey(self, name):
        ''' Returns the given key or None '''
        path = self.path.key + name

        if os.path.isfile(path):
            with open(path, 'rb') as f:
                return f.read()

        return None

    #########################################################
    # Misc
    #########################################################

    def __repr__(self):
        ''' Dump everything '''
        dic = dict(paths=self.path.contents, net=self.net.contents, info=self.info.contents, meta=str(self.meta))
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


def resolveMeta(nex, nexusType, mode):
    nex.meta.type = nexusType

    # support for passing strings or the enum value
    if isinstance(mode, str):
        nex.meta.mode = eval('Mode.%s' % mode)
    else:
        nex.meta.mode = mode

    '''
    Saving this here for later. Might want something more useful

    mode = args['--mode']
    if mode not in 'production development test local'.split():
        print 'You entered an invalid mode. Please enter one of [production, development, test, local]'
        exit(1)
    '''

    nex.meta.version = nex.__class__.VERSION


def resolveNetwork(nex, mode):
    ''' Given a nexus object and its mode, set its network values '''
    nex.net.webPort = eval('nex.__class__.PORT_HTTP_%s' % mode.name.upper())
    nex.net.port = eval('nex.__class__.PORT_WS_%s' % mode.name.upper())

    nex.net.webHost = eval('nex.__class__.HOST_HTTP_%s' % mode.name.upper())
    nex.net.host = eval('nex.__class__.HOST_WS_%s' % mode.name.upper())

    # Interpolating the websockets port into the url
    # TODO: take a look at this again
    nex.net.host = nex.net.host.replace('PORT', nex.net.port)


def resolveConfig(nex, mode):
    nex.conf.networkPool = nex.__class__.DYNAMIC_NETWORK_POOL
    nex.conf.pdconfdEnabled = nex.__class__.PDCONFD_ENABLED
    nex.conf.fcBounceUpdate = nex.__class__.FC_BOUNCE_UPDATE
    nex.conf.reservedChute = nex.__class__.RESERVED_CHUTE
    nex.conf.chuteSaveTimer = nex.__class__.FC_CHUTESTORAGE_SAVE_TIMER


def resolvePaths(nex):
    '''
    Are we on a VM? On snappy? Bare metal? The server?  So many paths, so few answers!
    '''

    # Default use the Home path (covers tools)
    nex.path.root = nex.__class__.PATH_HOME

    # Always use current directory when server (since there could be more than one of them )
    if nex.meta.type == Type.server:
        nex.path.root = nex.__class__.PATH_CURRENT

    # we can either resolve the root path based on the mode (which
    # is prefereable) or continue to just use the snappy check to set it
    # In other words, path_snappy if in snappy, else path_vm
    if nex.meta.type == Type.router:
        if nex.PATH_SNAPPY is None:
            nex.path.root = nex.__class__.PATH_LOCAL
        else:
            nex.path.root = nex.__class__.PATH_SNAPPY

    # Set boring paths
    nex.path.log = os.path.join(nex.path.root, nex.__class__.PATH_LOG)
    nex.path.key = os.path.join(nex.path.root, nex.__class__.PATH_KEY)
    nex.path.misc = os.path.join(nex.path.root, nex.__class__.PATH_MISC)
    nex.path.config = os.path.join(nex.path.root, nex.__class__.PATH_CONFIG)
    nex.path.docker = nex.__class__.DOCKER_BIN_DIR

    # Set old paths
    if nex.meta.mode == Mode.local:
        nex.path.pdconfdWrite = nex.__class__.PDCONFD_WRITE_DIR_LOCAL
        nex.path.uciConfig = nex.__class__.UCI_CONFIG_DIR_LOCAL
        nex.path.hostConfig = nex.__class__.HOST_CONFIG_PATH_LOCAL
    else:
        nex.path.pdconfdWrite = nex.__class__.PDCONFD_WRITE_DIR
        nex.path.uciConfig = nex.__class__.UCI_CONFIG_DIR
        nex.path.hostConfig = nex.__class__.HOST_CONFIG_PATH

    # create the paths
    for x in [nex.path.root, nex.path.log, nex.path.key, nex.path.misc]:
        if not os.path.exists(x):
            os.makedirs(x)


def resolveInfo(nexus, path):
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
        writeYaml(contents, path)

    nexus.info.pdid = contents['pdid']
    # nexus.info.owner = contents['version']


def overrideSettingsList(nexusClass, settings):
    '''
    Replaces constants settings values with new ones based on the passed list
    and THEN the environment variables as passed in
    '''

    # settings = {x.split(':')[0]: x.split(':')[1] for x in settings}

    # replace settings from dict first
    for x in settings:
        k, v = x.split(':')
    # for k, v in settings.iteritems():
        if getattr(nexusClass, k, None) is not None:
            setattr(nexusClass, k, v)
            output.out.info('Overriding setting %s with value %s from passed settings' % (k, v))
        else:
            raise KeyError('You have set a setting that does not exist! %s not found!' % k)


def overrideSettingsEnv(nexusClass):
    for v in dir(nexusClass):
        replace = os.environ.get(v, None)
        if replace is not None:
            output.out.info('Overriding setting %s with value %s from envionment variable' % (v, replace))
            setattr(nexusClass, v, replace)


def createDefaultInfo(path):
    default = {
        'version': 1,
        'pdid': None
    }

    writeYaml(default, path)


def validateInfo(contents):
    '''
    Error checking on the read YAML file. This is a temporary method.

    :
        param contents:
            the read - in yaml to check
    :
        type contents:
            dict.
    :
        returns:
            True if valid, else false
    '''
    INFO_REQUIRES = ['version', 'pdid']

    for k in INFO_REQUIRES:
        if k not in contents:
            output.out.err('Contents is missing: ' + str(k))
            return False

    return True


def writeYaml(contents, path):
    ''' Overwrites content with YAML representation at given path '''
    # print 'Writing ' + str(contents) + ' to path ' + str(path)

    with open(path, 'w') as f:
        f.write(yaml.dump(contents, default_flow_style=False))


def loadYaml(path):
    ''' Return dict from YAML found at path '''
    with open(path, 'r') as f:
        contents = yaml.load(f.read())

    # print 'Loaded ' + str(contents) + ' from path ' + str(path)
    return contents
