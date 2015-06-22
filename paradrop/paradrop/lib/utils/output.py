###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
lib.utils.output.
Helper for formatting output from Paradrop.
"""

import sys
import os as origOS
import traceback

from .pdutils import timestr, jsonPretty

# "global" variable all modules should be able to toggle
verbose = False

def logPrefix(*args, **kwargs):
    """Setup a default logPrefix for any function that doesn't overwrite it."""
    # Who called us?
    funcName = sys._getframe(1).f_code.co_name
    modName = origOS.path.basename(sys._getframe(1).f_code.co_filename).split('.')[0].upper()
    if(verbose):
        line = "(%d)" % sys._getframe(1).f_lineno
    else:
        line = ""
    
    if(args):
        return '[%s.%s%s @ %s %s]' % (modName, funcName, line, timestr(), ', '.join([str(a) for a in args]))
    else:
        return '[%s.%s%s @ %s]' % (modName, funcName, line, timestr())

class Colors:
    # Regular ANSI supported colors foreground
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Regular ANSI suported colors background
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # Other abilities
    BOLD = '\033[1m'
    
    # Ending sequence
    END = '\033[0m'
    
    # Color suggestions
    HEADER = BLUE
    VERBOSE = BLACK
    INFO = GREEN
    PERF = WHITE
    WARN = YELLOW
    ERR = RED
    SECURITY = BOLD + RED
    FATAL = BG_WHITE + RED

class IOutput:
    """Interface class that all Output classes should inherit."""
    def __call__(self, args):
        pass
    def __repr__(self):
        return "REPR"

class Fileout(IOutput):
    def __init__(self, filename, truncate=False):
        self.filename = filename
        self.mode = None
        if(truncate):
            self.mode = "w"
        else:
            self.mode = "a"
    def __call__(self, args):
        try:
            fd = open(self.filename, self.mode)
            # Make sure args is a str type
            if(not isinstance(args, str)):
                args = str(args)
            fd.write(args)
            fd.flush()
            fd.close()
        except:
            pass

class Stdout(IOutput):
    def __init__(self, color=None, other_out_types=None):
        self.color = color
        if(other_out_types and type(other_out_types) is not list):
            other_out_types = [other_out_types]
        self.other_out = other_out_types
    
    def __call__(self, args):
        # Make sure args is a str type
        if(not isinstance(args, str)):
            args = str(args) 
        msg = ""
        if(self.color):
            msg = self.color + args + Colors.END
        else:
            msg = args
        sys.stdout.write(msg)
        sys.stdout.flush()
        if self.other_out:
            for item in self.other_out:
                obj = item 
                obj(args)

class Stderr(IOutput):
    def __init__(self, color=None, other_out_types=None):
        self.color = color
        if(other_out_types and type(other_out_types) is not list):
            other_out_types = [other_out_types]
        self.other_out = other_out_types
    
    def __call__(self, args):
        # Make sure args is a str type
        if(not isinstance(args, str)):
            args = str(args)
        msg = ""
        if(self.color):
            msg = self.color + args + Colors.END
        else:
            msg = args
        sys.stderr.write(msg)
        sys.stderr.flush()
        if self.other_out:
            for item in self.other_out:
                obj = item 
                obj(args)

class OutException(IOutput):
    """
        This is a special call (out.exception()) that helps print exceptions
        quickly, easily and in the same format.
        Arguments:
            Exception object
            bool to print traceback
            logPrefix string
            kwargs : other important args you want us to know
    """
    def __init__(self, color=None, other_out_types=None):
        self.color = color
        if(other_out_types and type(other_out_types) is not list):
            other_out_types = [other_out_types]
        self.other_out = other_out_types
    
    def __call__(self, prefix, e, printTraceback, **kwargs):
        theTrace = "None"
        argStr = "None"
        if(kwargs):
            argStr = jsonPretty(kwargs)
        if(printTraceback):
            theTrace = traceback.format_exc()
        
        msg = "!! %s\nException: %s\nArguments: %s\nTraceback: %s\n" % (
            prefix, str(e), argStr, theTrace)
        # Format the message in a reasonable way
        msg = msg.replace('\n', '\n    ') + '\n'
        if(self.color):
            msg = self.color + msg + Colors.END
        
        sys.stderr.write(msg)
        sys.stderr.flush()
        if self.other_out:
            for item in self.other_out:
                obj = item 
                obj(args)

class FakeOutput(IOutput):
    def __call__(self, args):
        pass

class Output():
    """
        Class that allows stdout/stderr trickery.
        By default the paradrop object will contain an @out variable
        (defined below) and it will contain 2 members of "err" and "fatal".

        Each attribute of this class should be a function which points
        to a class that inherits IOutput(). We call these functions
        "output streams".

        The way this Output class is setup is that you pass it a series
        of kwargs like (stuff=OutputClass()). Then at any point in your
        program you can call "paradrop.out.stuff('This is a string\n')".

        This way we can easily support different levels of verbosity without
        the need to use some kind of bitmask or anything else.
        Literally you can define any kind of output call you want (paradrop.out.foobar())
        but if the parent script doesn't define the kwarg for foobar then the function
        call just gets thrown away.
        
        This is done by the __getattr__ function below, basically in __init__ we set
        any attributes you pass as args, and anything else not defined gets sent to __getattr__
        so that it doesn't error out.

        
        Currently these are the choices for Output classes:
            - StdoutOutput() : output sent to sys.stdout
            - StderrOutput() : output sent to sys.stderr
            - FileOutput()   : output sent to filename provided
    """
            
    def __init__(self, **kwargs):
        """Setup the initial set of output stream functions."""
        for name, func in kwargs.iteritems():
            setattr(self, name, func)
    
    def __getattr__(self, name):
        """Catch attribute access attempts that were not defined in __init__
            by default throw them out."""
        return FakeOutput()

    def __setattr__(self, name, val):
        """Allow the program to add new output streams on the fly."""
        if(verbose):
            print('>> Adding new Output stream %s' % name)
        # WARNING you cannot call setattr() here, it would recursively call back into this function
        self.__dict__[name] = val
    def __repr__(self):
        return "REPR"

# Create a standard out module to be used if no one overrides it
out = Output(
            header=Stdout(Colors.HEADER),
            verbose=FakeOutput(),
            info=Stdout(Colors.INFO),
            perf=Stdout(Colors.PERF),
            warn=Stdout(Colors.WARN),
            err=Stderr(Colors.ERR),
            exception=OutException(Colors.ERR),
            security=Stderr(Colors.SECURITY),
            fatal=Stderr(Colors.FATAL)
            )
