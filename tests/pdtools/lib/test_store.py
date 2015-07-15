'''
General lib tests
'''

import os

from pdtools.lib import store
import shutil

# Inject the correct testing directories
store.STORE_PATH = os.getcwd() + '/TESTS/'
store.LOG_PATH = store.STORE_PATH + 'logs/'
store.KEY_PATH = store.STORE_PATH + 'keys/'
store.INFO_PATH = store.STORE_PATH + 'root.yaml'


def testCreatesDirectories():
    s = store.Store()

    assert os.path.exists(store.STORE_PATH)
    assert os.path.exists(store.LOG_PATH)
    assert os.path.exists(store.KEY_PATH)
    assert os.path.exists(store.INFO_PATH)

    cleanup()


def testYamlSave():
    target = os.getcwd() + '/y.yaml'
    args = {'a':'b', 'c':['d', 'e', 'f']}

    store.writeYaml(args, target)
    assert store.loadYaml(target) == args

    os.remove(target)

def testYamlCorruption():
    ''' Corrupted or missing information in the saved file '''
    args = {'version':'b', 'accounts':['d', 'e', 'f']}

    assert store.sanityCheck(args) == False

def cleanup():
    os.remove(store.INFO_PATH)
    shutil.rmtree(store.LOG_PATH)
    shutil.rmtree(store.KEY_PATH)
    shutil.rmtree(store.STORE_PATH)
