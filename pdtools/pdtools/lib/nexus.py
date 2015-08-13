'''
Stateful, singleton, command and control center. 

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
'''

import os

# Havent done the singleton yet. Didn't see a need.
# ref = None


class Nexus(object):

    def __init__(self, type, devMode=False):
        '''
        :param type: one of [router, tool, server]
        :type type: str.
        :param devMode: uses dev mode if set. Could mean anything, but at the very least it
            changes the ports and hostname
        '''
        self.type, self.devMode = type, devMode

        # initialize the paths
        self.makePaths()
        self.load()

    def onStart(self):
        pass

    def onStop(self):
        pass

    def makePaths(self):
        '''
        Are we on a VM? On snappy? Bare metal? The server? 
        So many paths, so few answers!
        '''

        # Lets start out being a router
        self.rootPath = os.getenv("SNAP_APP_USER_DATA_PATH", None)

        # Put tools contents in the home directory
        if self.type is 'tool':
            self.rootPath = expanduser('~') + '/.paradrop/'

        # Current directory (since we might have more than one server at a time)
        elif self.type is 'server':
            self.rootPath = os.getcwd() + '/.paradrop/'

        # We're a router, yay! But are we a router on snappy or local? The snappy
        # path will not resolve on a local machine-- let it fall through, we're set
        elif not self.rootPath:
            self.rootPath = expanduser('~') + '/.paradrop/local/'

        # Set the boring paths
        self.logPath = self.rootPath + 'logs/'
        self.keyPath = self.rootPath + 'keys/'
        self.miscPath = self.rootPath + 'misc/'
        self.configPath = self.rootPath + 'config'  # This is the only 'path' that is really a file

        # create the paths
        for x in [self.rootPath, self.logPath, self.keyPath, self.miscPath]:
            if not os.path.exists(x):
                os.makedirs(x)

    def save():
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
