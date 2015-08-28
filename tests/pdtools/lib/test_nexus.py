
import os
import shutil

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

    assert nex.net.host == nexus.NexusBase.HOST_WS_PRODUCTION
    assert nex.net.port == nexus.NexusBase.PORT_WS_PRODUCTION
    assert nex.net.webHost == nexus.NexusBase.HOST_HTTP_PRODUCTION
    assert nex.net.webPort == nexus.NexusBase.PORT_HTTP_PRODUCTION


def testAccessVariables():
    ''' Variable access should be handled through the internal "interceptor" methods '''
    pass
