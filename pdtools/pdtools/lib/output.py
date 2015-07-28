###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
Output mapping, capture, storange, and display.

Some of the methods and choice here may seem strange -- they are meant to
keep this file in
"""

import sys
import traceback
import Queue
import threading
import time
import colorama
import traceback

from pdtools.lib import pdutils

from twisted.python.logfile import DailyLogFile
from twisted.python import log

# "global" variable all modules should be able to toggle
verbose = False

# colorama package does colors but doesn't do style, so keeping this for now
BOLD = '\033[1m'

# Represents formatting information for the specified log type
LOG_TYPES = {
    'HEADER': {'name': 'HEADER', 'glyph': '==', 'color': colorama.Fore.BLUE},
    'VERBOSE': {'name': 'VERBOSE', 'glyph': '>>', 'color': colorama.Fore.BLACK},
    'INFO': {'name': 'INFO', 'glyph': '--', 'color': colorama.Fore.GREEN},
    'PERF': {'name': 'PERF', 'glyph': '--', 'color': colorama.Fore.WHITE},
    'WARN': {'name': 'WARN', 'glyph': '**', 'color': colorama.Fore.YELLOW},
    'ERR': {'name': 'ERR', 'glyph': '!!', 'color': colorama.Fore.RED},
    'SECURITY': {'name': 'SECURITY', 'glyph': '!!', 'color': BOLD + colorama.Fore.RED},
    'FATAL': {'name': 'FATAL', 'glyph': '!!', 'color': colorama.Back.WHITE + colorama.Fore.RED},
}

###############################################################################
# Logging Utilities
###############################################################################


def silentLogPrefix(stepsUp):
    '''
    logPrefix v2-- gets caller information silently (without caller intervention)
    The single parameter reflects how far up the stack to go to find the caller and
    depends how deep the direct caller to this method is wrt to the target caller

    NOTE: Some calls cannot be silently prefixed (getting into the twisted code is a 
    great example)

    :param steps: the number of steps to move up the stack for the caller
    :type steps: int.
    '''

    try:
        trace = sys._getframe(stepsUp).f_code.co_filename
        line = sys._getframe(stepsUp).f_lineno
        module, package = parseLogPrefix(trace)
    except:
        return 'unknown', 'unknown', '??'

    return package, module, line


def parseLogPrefix(tb):
    '''
    Takes a traceback returned by 'extract_tb' and returns the package, module, 
    and line number
    '''
    path = tb.split('/')
    module = path[-1].replace('.py', '')
    package = path[-2]

    return module, package


class PrintLogThread(threading.Thread):

    '''
    All file printing access from one thread.

    Receives information when its placed on the passed queue.
    Called from one location: Output.handlePrint.

    Does not close the file: this happens in Output.endLogging. This 
    simplifies the operation of this class, since it only has to concern
    itself with the queue. 

    The path must exist before DailyLog runs for the first time.
    '''

    def __init__(self, path, queue, name='log'):
        threading.Thread.__init__(self)
        self.queue = queue
        self.writer = DailyLogFile(name, path)

        # Don't want this to float around if the rest of the system goes down
        self.setDaemon(True)

    def run(self):
        while True:
            result = self.queue.get(block=True)

            try:
                writable = pdutils.json2str(result)
                self.writer.write(writable + '\n')
                self.writer.flush()
            except:
                pass

            self.queue.task_done()


class OutputRedirect(object):

    """
    Intercepts passed output object (either stdout and stderr), calling the provided callback
    method when input appears.

    Retains the original mappings so writing can still happen. Performs no formatting.
    """

    def __init__(self, output, contentAppearedCallback, logType):
        self.callback = contentAppearedCallback
        self.trueOut = output
        self.type = logType

    def trueWrite(self, contents):
        ''' Someone really does want to output'''
        formatted = str(contents)

        # print statement ususally handles these things
        if len(formatted) == 0 or formatted[-1] is not '\n':
            formatted += '\n'

        self.trueOut.write(formatted)

    def write(self, contents):
        '''
        Intercept output to the assigned target and callback with it. The true output is
        returned with the callback so the delegate can differentiate between captured outputs
        in the case when two redirecters are active.
        '''
        if contents == '\n':
            return

        package, module, line = silentLogPrefix(2)

        ret = {'message': str(contents.strip()), 'type': self.type['name'], 'extra': {'details': 'floating print statement'},
               'package': package, 'module': module, 'timestamp': time.time(),
               'owner': 'UNSET', 'line': line, 'pdid': 'pd.damouse.example'}

        self.callback(ret)

###############################################################################
# Output Classes
###############################################################################


class BaseOutput(object):

    '''
    Base output type class.

    This class and its subclasses are registered with an attribute on the global
    'out' function and is responsible for formatting the given output stream
    and returning it as a "log structure" (which is a dict.)

    For example:
        out.info("Text", anObject)

    requires a custom object to figure out what to do with anObject where the default case will simply
    parse the string with an appropriate color.

    Objects are required to output a dict that mininmally contains the keys message and type.
    '''

    def __init__(self, logType):
        '''
        Initialize this output type.

        :param logType: how this output type is displayed
        :type logType: dictionary object containing name, glyph, and color keys
        '''

        self.type = logType

    def __call__(self, args, logPrefixLevel=3):
        '''
        Called as an attribute on out. This method takes the passed params and builds a log dict,
        returning it.

        Subclasses can customize args to include whatever they'd like, adding content
        under the key 'extras.' The remaining keys should stay in place.
        '''
        package, module, line = silentLogPrefix(3)

        # String newlines
        if args[-1] == '\n':
            args = args.strip()

        ret = {'message': str(args), 'type': self.type['name'], 'extra': {},
               'package': package, 'module': module, 'timestamp': time.time(),
               'owner': 'UNSET', 'line': line, 'pdid': 'pd.damouse.example'}

        return ret

    def formatOutput(self, logDict):
        '''
        Convert a logdict into a custom formatted, human readable version suitable for
        printing to console.
        '''
        trace = '[%s.%s#%s @ %s] ' % (logDict['package'], logDict['module'], logDict['line'], pdutils.timestr(logDict['timestamp']))
        return self.type['color'] + self.type['glyph'] + ' ' + trace + logDict['message'] + colorama.Style.RESET_ALL

    def __repr__(self):
        return "REPR"


class TwistedOutput(BaseOutput):

    def __call__(self, args):
        '''
        Catch twisted logs and make them fall inline with our logs.

        Ignore exceptions (those get their own handler)

        Twisted will always pass a dict and guarantees [message, isError, and printed]
        will be in there. 
        '''

        # there is another class responsible for handling error messages. Ignore these.
        if args['isError'] == 1:
            return None

        # Start with the default message, but just grab the whole thing if it doesn't work
        try:
            message = args['message'][0]
        except:
            message = str(args)

        # NOTE: This code gets the REAL twisted stack trace-- but it seems to
        # make things more noisy without actually helping
        # package, module, line = silentLogPrefix(5)

        # ret = {'message': message, 'type': self.type['name'], 'extra': {},
        #        'package': package, 'module': module, 'timestamp': time.time(),
        #        'owner': 'UNSET', 'line': line, 'pdid': 'pd.damouse.example'}

        ret = {'message': message, 'type': self.type['name'], 'extra': {},
               'package': 'twisted', 'module': 'internal', 'timestamp': time.time(),
               'owner': 'UNSET', 'line': '??', 'pdid': 'pd.damouse.example'}

        return ret


class TwistedException(BaseOutput):

    def __call__(self, args):
        '''
        Catch twisted logs and make them fall inline with our logs.

        Only catch errors.

        Twisted will always pass a dict and guarantees [message, isError, and printed]
        will be in there. 
        '''

        if args['isError'] == 0:
            return None

        # special handling of exception prefix logging
        try:
            tb = args['failure'].getTracebackObject()
            stacktrace = traceback.extract_tb(tb)[-1]

            package, module = parseLogPrefix(stacktrace[0])
            line = stacktrace[1]
        except Exception:
            package, module, line = "uknown", 'unknown', '??'

        # message =

        ret = {'message': str(args['failure'].getTraceback().strip()), 'type': self.type['name'], 'extra': {'details': 'floating print statement'},
               'package': package, 'module': module, 'timestamp': time.time(),
               'owner': 'UNSET', 'line': line, 'pdid': 'pd.damouse.example'}

        return ret


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

        --v2 Changes--
        v1 implementation relied on seperate Writers for each output stream, which
        helped with threading issues. Outputs were open and closed for each write, which is
        wildly expensive (300ms on local bench!)

        In v2, all contents are logged to file. Writing occurs on a dedicated thread that holds its files
        open. All print functions are routed through a format transformer and then the printer.
    """

    def __init__(self, **kwargs):
        """Setup the initial set of output stream functions."""

        # Begins intercepting output and converting ANSI characters to win32 as applicable
        colorama.init()

        # Refactor this as an Output class
        self.__dict__['redirectErr'] = OutputRedirect(sys.stderr, self.handlePrint, LOG_TYPES['VERBOSE'])
        self.__dict__['redirectOut'] = OutputRedirect(sys.stdout, self.handlePrint, LOG_TYPES['VERBOSE'])

        # Setattr wraps the output objects in a
        # decorator that allows this class to intercept their output, This dict holds the
        # original objects.
        self.__dict__['outputMappings'] = {}

        for name, func in kwargs.iteritems():
            setattr(self, name, func)

    def __getattr__(self, name):
        """Catch attribute access attempts that were not defined in __init__
            by default throw them out."""

        # raise NotImplementedError("You must create " + name + " to log with it")
        pass

    def __setattr__(self, name, val):
        """Allow the program to add new output streams on the fly."""
        if(verbose):
            print 'Adding new Output stream %s' % name

        def inner(*args, **kwargs):
            result = val(*args, **kwargs)
            self.handlePrint(result)
            return result

        # can't call setattr here (which normally looks like self.name = inner)
        self.__dict__[name] = inner

        # Save the original function (unwrapped) under the tag its registered with
        # so we can later query the objects by this tag and ask them to print
        self.__dict__['outputMappings'][name] = val

    def __repr__(self):
        return "REPR"

    def startLogging(self, filePath=None, stealStdio=False, printToConsole=True):
        '''
        Begin logging. The output class is ready to go out of the box, but in order
        to prevent mere imports from stealing stdio or console logging to vanish
        these must be manually turned on.

        :param filePath: if provided, begin logging to the given directory. If 
            not provided, do not write out logs.
        :type filePath: str
        :param stealStdio: choose to intercept stdio (including vanilla print
            statements) or allow it to passthrough
        :type stealStdio: bool.
        :param printToConsole: output the results of all logging to the console. This
            is primarily a performance consideration when running in production
        :type printToConsole: bool.

        '''
        # by default, stdio gets captures. This can be toggled off
        self.stealStdio(stealStdio)
        self.logToConsole(printToConsole)

        # Override twisted logging (allows us to cleanly catch all exceptions)
        # This must come after the setattr calls so we get the wrapped object
        log.startLoggingWithObserver(self.twisted, setStdout=False)
        log.startLoggingWithObserver(self.twistedErr, setStdout=False)

        if filePath is not None:
            self.__dict__['queue'] = Queue.Queue()
            self.__dict__['printer'] = PrintLogThread(filePath, self.queue)
            self.printer.start()

    def endLogging(self):
        '''
        Ask the printing thread to flush and end, then return.
        '''

        out.info('Asking file logger to close')
        self.queue.join()

        # Because the print thread can't tell when it goes down as currently designed
        self.printer.writer.close()

    def handlePrint(self, logDict):
        '''
        All printing objects return their messages. These messages are routed
        to this method for handling.

        Send the messages to the printer. Optionally display the messages. 
        Decorate the print messages with metadata.

        :param logDict: a dictionary representing this log item. Must contain keys
        message and type.
        :type logDict: dict.
        '''

        # If the logger returns None, assume we dont want the output
        if logDict is None:
            return

        # write out the log message to file
        if self.queue is not None:
            self.queue.put(logDict)

        # Write out the human-readable version to out if needed (but always print out 
        # exceptions for testing purposes)
        if self.printLogs or logDict['type'] == 'ERR':
            res = self.messageToString(logDict)
            self.redirectOut.trueWrite(res)

    def messageToString(self, message):
        '''
        Converts message dicts to a format suitable for printing based on 
        the conversion rules laid out in in that class's implementation.

        :param message: the dict to convert to string
        :type message: dict.
        :returns: str 
        '''

        outputObject = self.outputMappings[message['type'].lower()]
        return outputObject.formatOutput(message)

    ###############################################################################
    # Reconfiguration
    ###############################################################################
    def stealStdio(self, newStatus):
        self.__dict__['stealIo'] = newStatus

        if newStatus:
            # assign our interceptor objects to the outputs
            sys.stdout = self.redirectOut
            sys.stderr = self.redirectErr
        else:
            # return stdout and err to their respective positions
            sys.stdout = self.__dict__['redirectOut'].trueOut
            sys.stderr = self.__dict__['redirectErr'].trueOut

    def logToConsole(self, newStatus):
        self.__dict__['printLogs'] = newStatus


out = Output(
    header=BaseOutput(LOG_TYPES['HEADER']),
    testing=BaseOutput(LOG_TYPES['VERBOSE']),
    verbose=BaseOutput(LOG_TYPES['VERBOSE']),
    info=BaseOutput(LOG_TYPES['INFO']),
    perf=BaseOutput(LOG_TYPES['PERF']),
    warn=BaseOutput(LOG_TYPES['WARN']),
    err=BaseOutput(LOG_TYPES['ERR']),
    exception=BaseOutput(LOG_TYPES['ERR']),
    security=BaseOutput(LOG_TYPES['SECURITY']),
    fatal=BaseOutput(LOG_TYPES['FATAL']),
    twisted=TwistedOutput(LOG_TYPES['INFO']),
    twistedErr=TwistedException(LOG_TYPES['ERR'])
)
