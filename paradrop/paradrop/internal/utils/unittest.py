###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import traceback, subprocess
import os as origOS
import shutil as origShutil

THEPATH = ""
def getPath(module):
    return "/tmp/%s" % module

# The main module can choose to change this, which would mean that all the @decorator functions are activated below
testing = False

def fixmount(func):
    """@decorator
        Throw away whatever openwrt module was doing and return a different string always."""
    def newFunc():
        out.unittest('~~ [UNITTEST] Override %s\n' % func.__name__)
        return "mount -o loop"
    
    if(testing):
        return newFunc
    else:
        return func

def fixopen(func):
    """@decorator
        Throw away whatever openwrt module was doing and return a different string always."""
    def newFunc(p, mode):
        p = "%s%s" % (THEPATH, p)
        out.unittest('~~ [UNITTEST] Override %s\n' % func.__name__)
        return func(p, mode)
    
    if(testing):
        return newFunc
    else:
        return func

def fixpath(func):
    """@decorator
        Function that should be called by anything a unittest might need to fix.
        What this does is transparently replaces the path to what the unit test
        would use so '/tmp' => '/path/to/test/stuff/tmp'
        """
    def newFunc(*args):
        if(args):
            largs = []
            for a in args:
                largs.append("%s%s" % (THEPATH, a))
            args = tuple(largs)
        out.unittest('~~ [UNITTEST] Override %s\n' % func.__name__)
        return func(*args)
    
    if(testing):
        return newFunc
    else:
        return func

def fixoscall(func):
    """@decorator
        Function that should be called by any function that performs a oscall as its primary feature.
        What this does is transparently replaces the function with just text output
        saying what would happen.
        """
    def newFunc(*args):
        out.unittest('~~ [UNITTEST] Override %s\n' % func.__name__)
        # The reload functions are designed to return True on error and False otherwise
        return False
    
    if(testing):
        return newFunc
    else:
        return func

def setupOpenWrtEnv(basePath, configPath):
    """Sets up the commonly found directories in our temp FS that we might use."""
    try:
        # Check if temp path exists first, if so delete it so we're fresh
        if(origOS.path.exists(basePath)):
            origShutil.rmtree(basePath)
        # Make the temp dir for this test
        origOS.makedirs(basePath)
    except Exception as e:
        out.fatal("!! Unable to make temp path for %s\n" % basePath)
        print(str(e))
        exit()
    # Now rebuild a new path
    try:
        origOS.mkdir(basePath + "/tmp")
        origOS.mkdir(basePath + "/dev")
        origOS.mkdir(basePath + "/root")
        origOS.mkdir(basePath + "/mnt")
        origOS.mkdir(basePath + "/etc")
        origOS.mkdir(basePath + "/etc/config")
        origOS.mkdir(basePath + "/var")
        origOS.mkdir(basePath + "/var/lib")
        origOS.mkdir(basePath + "/var/lib/lxc")

        # Now copy over the openwrt config files to the /etc/config dir
        import glob
        cfgs = glob.glob(configPath + "*")
        for c in cfgs:
            filename = origOS.path.basename(c)
            dst = "%s/etc/config/%s" % (basePath, filename)
            origShutil.copyfile(c, dst)
    except Exception as e:
        out.fatal("!! [UNITTEST] Unable to setup temp directories %s\n" % str(e))
        print(traceback.format_exc())
        exit()

def unmountAll(*args):
    for a in args:
        if(origOS.path.ismount(a)):
            out.unittest('-- Unmounting %s mount path in unit test directory\n' % a)
            proc = subprocess.Popen("umount %s" % a, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, errors = proc.communicate()

            if(proc.returncode):
                out.warn("!! Unable to create disk blob for unit test (%d) %s\n" % (proc.returncode, errors))
                exit(0)

def fixThePath(thep, p):
    # first add all components of path together
    t = '%s/%s' % (thep, p)
    # Now when we 'normalize' it all will be fixed
    return origOS.path.normpath(t)

def addAttrs(obj, module):
    """Takes all attributes from @module (as given by dir) and sets them to @obj, then returns it."""
    try:
        for d in dir(module):
            # Make sure we don't get the __vars__
            if("__" in d):
                continue
            setattr(obj, d, getattr(module, d))
        return obj
    except:
        print('!! Unable to addAttrs from: %s' % module.__class__.__name__)
        return None

def replaceAttrs(obj1, obj2, attrs):
    """Look at a list of strings which represents attributes.
        If obj2 contains that attr, then set obj1 to be the value from obj2."""
    try:
        for d in attrs:
            if(d in dir(obj2)):
                setattr(obj1, d, getattr(obj2, d))
        return obj1
    except:
        print('!! Unable to addAttrs from: %s' % obj2.__class__.__name__)
        return None


