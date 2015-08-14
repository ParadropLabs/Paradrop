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
'''

import os

from twisted.internet import reactor

from pdtools.lib import store, riffle, output

# Global singleton. Must be assigned when the object is created
core = None


class NexusBase(object):

    def __init__(self, nexType, devMode=False, stealStdio=True, printToConsole=True):
        '''
        The one big thing this function leaves out is reactor.start(). Call this externally 
        *after* initializing a nexus object. 

        :param type: one of [router, tool, server]
        :type type: str.
        :param devMode: uses dev mode if set. Could mean anything, but at the very least it
            changes the ports and hostname
        '''

        self.type, self.devMode = nexType, devMode

        # initialize the paths
        self.makePaths()
        self.load()

        # initialize output. If filepath is set, logs to file.
        # If stealStdio is set intercepts all stderr and stdout and interprets it internally
        # If printToConsole is set (defaults True) all final output is rendered to stdout
        output.out.startLogging(filePath=self.logPath, stealStdio=True, printToConsole=printToConsole)

        # register onStop for the shutdown call
        reactor.addSystemEventTrigger('before', 'shutdown', self.onStop)
        reactor.callLater(0, self.onStart)

    def onStart(self):
        output.out.usage('%s coming up' % self.type)

    def onStop(self):
        output.out.usage('%s going down' % self.type)

        output.out.endLogging()

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
        self.logPath = self.rootPath + 'logs/'
        self.keyPath = self.rootPath + 'keys/'
        self.miscPath = self.rootPath + 'misc/'
        self.configPath = self.rootPath + 'config'  # This is the only 'path' that is really a file

        output.out.err('Using root path: ' + str(self.rootPath))

        # create the paths
        for x in [self.rootPath, self.logPath, self.keyPath, self.miscPath]:
            if not os.path.exists(x):
                os.makedirs(x)

    def load(self):
        pass

    def save(self):
        ''' Ehh. Ideally this should happen constantly and asynchronously. '''
        pass

    #########################################################
    # Settings
    #########################################################

    def setSetting(self, k, v):
        pass

    def getSetting(self, k):
        pass

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
        ''' Different in production vs dev, etc. Returns a host, port tuple '''
        pass

    def rifflePort(self):
        pass

    def insecureRifflePort(self):
        ''' This isnt a thing yet. But it will be. '''
        pass

    def webPort(self):
        ''' If serving on something other than 80 '''
        pass

    #########################################################
    # Path Resolution
    #########################################################

    def logPath():
        pass

    def keyPath():
        pass

    def chutePath():
        pass

    #########################################################
    # Utils
    #########################################################
