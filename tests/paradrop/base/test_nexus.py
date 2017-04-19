import os
import shutil

from nose.tools import assert_raises
from paradrop.lib.utils import pdos
from paradrop.base import nexus, settings


class TestingNexus(nexus.NexusBase):
    pass


def setup():
    settings.loadSettings(mode="unittest")


def teardown():
    pdos.remove(settings.CONFIG_HOME_DIR)


###############################################################################
# Settings Assignment, Paths
###############################################################################


def testMetaAssignment():
    nex = TestingNexus()
    assert nex.info.version == 1


def testConfigLoadingEmpty():
    nex = TestingNexus()
    assert nex.info.pdid == None


def testConfigLoadingExisting():
    contents = dict(pdid='pd.damouse.aardvark', version=1, pdserver='http://paradrop.org', wampRouter='ws://paradrop.org:9080/ws')
    nexus.writeYaml(contents, settings.CONFIG_FILE)

    nex = TestingNexus()
    assert nex.info.pdid == 'pd.damouse.aardvark'
    assert nex.info.pdserver == 'http://paradrop.org'
    assert nex.info.wampRouter == 'ws://paradrop.org:9080/ws'
    pdos.remove(settings.CONFIG_FILE)


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
    nex = TestingNexus()
    nex.info.a = 1

    dic = nexus.loadYaml(settings.CONFIG_FILE)
    assert dic['a'] == 1

