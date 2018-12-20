'''
Stateful, singleton, paradrop daemon command center.
See docstring for NexusBase class for information on settings.

SETTINGS QUICK REFERENCE:
    # assuming the following import
    from paradrop.base import nexus

    nexus.core.info.version
    nexus.core.info.pdid
'''

import os
import yaml
import json

import smokesignal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

from . import output, settings
from paradrop.lib.utils import pdosq

# Global access. Assign this wherever you instantiate the Nexus object:
#       nexus.core = MyNexusSubclass()
core = None


class NexusBase(object):
    '''
    Resolving these values to their final forms:
        1 - module imported, initial values assigned(as written below)
        2 - class is instatiated, passed settings to replace values
        3 - instance chooses appropriate values based on current state(production or local)
            Each category has its own method for initialization here
            (see: resolveNetwork, resolvePaths)

    '''
    VERSION = 1                                         # nexus.core.info.version
    PDID = None                                         # nexus.core.info.pdid


    def __init__(self, stealStdio=True, printToConsole=True):
        '''
        The one big thing this function leaves out is reactor.start(). Call this externally
        *after * initializing a nexus object.
        '''
        self.session = None
        self.wamp_connected = False
        self.jwt_valid = False

        self.info = AttrWrapper()
        resolveInfo(self, settings.CONFIG_FILE)
        self.info.setOnChange(self.onInfoChange)

        # initialize output. If filepath is set, logs to file.
        # If stealStdio is set intercepts all stderr and stdout and interprets it internally
        # If printToConsole is set (defaults True) all final output is rendered to stdout
        output.out.startLogging(filePath=settings.LOG_DIR, stealStdio=stealStdio, printToConsole=printToConsole)

        # register onStop for the shutdown call
        reactor.addSystemEventTrigger('before', 'shutdown', self.onStop)

        # The reactor needs to be runnnig before this call is fired, since we start the session
        # here. Assuming callLater doesn't fire until thats happened
        reactor.callLater(0, self.onStart)


    def onStart(self):
        pdid = self.info.pdid if self.provisioned() else 'UNPROVISIONED'
        output.out.usage('%s coming up' % (pdid))


    def onStop(self):
        self.save()

        output.out.usage('%s going down' % (self.info.pdid))
        smokesignal.clear_all()
        output.out.endLogging()


    @inlineCallbacks
    def connect(self, sessionClass, debug=False):
        '''
        Takes the given session class and attempts to connect to the crossbar fabric.

        If an existing session is connected, it is cleanly closed.
        '''

        if (self.session is not None):
            yield self.session.leave()

        self.wamp_connected = False

        output.out.info('Connecting to wamp router at URI: %s' % str(self.info.wampRouter))

        # Setting self.session here only works for the first connection but
        # becomes stale if the connection fails and we reconnect.
        # In that case a new session object is automatically created.
        # For this reason, we also update this session reference in BaseSession.onJoin.
        self.session = yield sessionClass.start(self.info.wampRouter, self.info.pdid, debug=debug)
        returnValue(self.session)


    def onInfoChange(self, key, value):
        '''
        Called when an internal setting is changed. Trigger a save automatically.
        '''
        self.save()


    def save(self):
        ''' Ehh. Ideally this should happen asynchronously. '''
        saveDict = self.info.__dict__['contents']
        saveDict['version'] = self.info.version

        writeYaml(saveDict, settings.CONFIG_FILE)

    #########################################################
    # High Level Methods
    #########################################################

    def provisioned(self):
        '''
        Checks if this[whatever] appears to be provisioned or not
        '''

        return self.info.pdid is not None

    def provision(self, pdid, pdserver=settings.PDSERVER, wampRouter=settings.WAMP_ROUTER):
        self.info.pdid = pdid
        self.info.pdserver = pdserver
        self.info.wampRouter = wampRouter

    #########################################################
    # Keys
    #########################################################

    def saveKey(self, key, name):
        ''' Save the key with the given name. Overwrites by default '''
        path = settings.KEY_DIR + name

        with open(path, 'wb') as f:
            f.write(key)

    def getKey(self, name):
        ''' Returns the given key or None '''
        path = settings.KEY_DIR + name

        if os.path.isfile(path):
            with open(path, 'rb') as f:
                return f.read()

        return None

    #########################################################
    # Misc
    #########################################################

    def __repr__(self):
        ''' Dump everything '''
        dic = dict(info=self.info.contents)
        return json.dumps(dic, sort_keys=True, indent=4)

#########################################################
# Utils
#########################################################

class AttrWrapper(object):
    '''
    Simple attr interceptor to make accessing settings simple.

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


def resolveInfo(nexus, path):
    '''
    Given a path to the config file, load its contents and assign it to the
    config file as appropriate.
    '''

    # Check to make sure we have a default settings file
    if not os.path.isfile(path):
        createDefaultInfo(path)

    contents = pdosq.read_yaml_file(path)

    # Sanity check contents of info and throw it out if bad
    if not validateInfo(contents):
        output.out.err('Saved configuration data invalid, destroying it.')
        os.remove(path)
        createDefaultInfo(path)
        contents = pdosq.read_yaml_file(path, default={})
        writeYaml(contents, path)

    nexus.info.pdid = contents['pdid']
    nexus.info.version = contents['version']
    nexus.info.pdserver = contents['pdserver']
    nexus.info.wampRouter = contents['wampRouter']


def createDefaultInfo(path):
    default = {
        'version': 1,
        'pdid': None,
        'pdserver': settings.PDSERVER,
        'wampRouter': settings.WAMP_ROUTER
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
    INFO_REQUIRES = ['version', 'pdid', 'pdserver', 'wampRouter']

    for k in INFO_REQUIRES:
        if k not in contents:
            output.out.err('Contents is missing: ' + str(k))
            return False

    return True


def writeYaml(contents, path):
    ''' Overwrites content with YAML representation at given path '''
    # print 'Writing ' + str(contents) + ' to path ' + str(path)

    with open(path, 'w') as f:
        f.write(yaml.safe_dump(contents, default_flow_style=False))
