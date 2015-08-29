
import os
import shutil

from nose.tools import assert_raises

from pdtools.lib import nexus


root = os.getcwd() + '/TESTS/'


class TestingNexus(nexus.NexusBase):
    pass


def setup():
    # nexus.core = TestingNexus()
    nexus.NexusBase.PATH_SNAPPY = root


def teardown():
    nexus.core = None

    shutil.rmtree(root)

    assert not os.path.exists(root)

###############################################################################
# Settings Assignment
###############################################################################


def testMetaAssignment():
    nex = TestingNexus(nexus.Type.router, nexus.Mode.production)

    assert nex.meta.type == nexus.Type.router
    assert nex.meta.mode == nexus.Mode.production
    assert nex.meta.version == 1


def testPathCreation():
    nex = TestingNexus(nexus.Type.router, nexus.Mode.production)

    assert nex.paths.root == root
    assert nex.paths.log == root + nexus.NexusBase.PATH_LOG
    assert nex.paths.key == root + nexus.NexusBase.PATH_KEY
    assert nex.paths.misc == root + nexus.NexusBase.PATH_MISC
    assert nex.paths.config == root + nexus.NexusBase.PATH_CONFIG


def testNetworkResolution():
    nex = TestingNexus(nexus.Type.router, nexus.Mode.production)

    repl = nexus.NexusBase.HOST_WS_PRODUCTION.replace('PORT', nex.net.port)
    assert nex.net.host == repl
    assert nex.net.port == nexus.NexusBase.PORT_WS_PRODUCTION
    assert nex.net.webHost == nexus.NexusBase.HOST_HTTP_PRODUCTION
    assert nex.net.webPort == nexus.NexusBase.PORT_HTTP_PRODUCTION


def testConfigLoadingEmpty():
    nex = TestingNexus(nexus.Type.router, nexus.Mode.production)
    assert nex.info.pdid == None


def testConfigLoadingExisting():
    contents = dict(pdid='pd.damouse.aardvark', version=1)
    nexus.writeYaml(contents, root + nexus.NexusBase.PATH_CONFIG)

    nex = TestingNexus(nexus.Type.router, nexus.Mode.production)
    assert nex.info.pdid == 'pd.damouse.aardvark'


###############################################################################
# AttrWrapper
###############################################################################

def testWrapperDoesntAllowChanges():
    wrapper = nexus.AttrWrapper()

    wrapper.a = 1
    assert wrapper.a == 1

    def s():
        wrapper._lock()
        wrapper.a = 2

    assert_raises(AttributeError, s)

###############################################################################
# Setings Changes
###############################################################################


def testSaveCallbackTriggered():
    class Receiver:

        def __init__(self):
            self.received = False

        def onChange(self, k, v):
            self.received = True

    rec = Receiver()

    wrapper = nexus.AttrWrapper()
    wrapper.a = 1

    wrapper.setOnChange(rec.onChange)

    wrapper.a = 2

    assert wrapper.a == 2
    assert rec.received == True


def testSaveUpdatesYaml():
    nex = TestingNexus(nexus.Type.router, nexus.Mode.production)
    nex.info.a = 1

    dic = nexus.loadYaml(root + nexus.NexusBase.PATH_CONFIG)
    assert dic['a'] == 1


def testWrappersLocked():
    nex = TestingNexus(nexus.Type.router, nexus.Mode.production)

    def s(wrapper):
        wrapper.a = 2

    assert_raises(AttributeError, s, nex.paths)
    assert_raises(AttributeError, s, nex.net)
    assert_raises(AttributeError, s, nex.meta)


###############################################################################
# Setings Overrides
###############################################################################

def testOverrideWithList():
    replace = dict(PORT_WS_PRODUCTION='5555')

    nex = TestingNexus(nexus.Type.router, nexus.Mode.production, settings=replace)
    print nex
    assert nex.net.port == '5555'


def testOverrideWithEnv():
    os.environ["PORT_WS_DEVELOPMENT"] = "5555"

    nex = TestingNexus(nexus.Type.router, nexus.Mode.development)
    print nex
    assert nex.net.port == '5555'

def testOverrideWithSubclass():
    ''' I really dont like this functionality, but meh. '''
    class Over(nexus.NexusBase):
        PORT_WS_PRODUCTION = '1111'

    nex = Over(nexus.Type.router, nexus.Mode.production)
    assert nex.net.port == '1111'