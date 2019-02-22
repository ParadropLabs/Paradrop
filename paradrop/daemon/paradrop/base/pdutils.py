###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
lib.utils.output.
Helper for formatting output from Paradrop.
"""
from __future__ import print_function

import time
import json
import urllib

import six

timeflt = lambda: time.time()
timeint = lambda: int(time.time())
timestr = lambda x=None: time.asctime(time.localtime(x)) if x else time.asctime()

# Short time string
stimestr = lambda x=None: time.strftime('%a %H:%M', time.localtime(x))


def timedur(x):
    """
        Print consistent string format of seconds passed.
        Example: 300 = '5 mins'
        Example: 86400 = '1 day'
        Example: 86705 = '1 day, 5 mins, 5 sec'
    """
    divs = [('days', 86400), ('hours', 3600), ('mins', 60)]
    x = float(x)
    res = []
    for lbl, sec in divs:
        if(x >= sec):
            rm, x = divmod(x, float(sec))
            # If exactly 1, remove plural of label
            if(rm == 1.0):
                res.append((lbl[:-1], int(rm)))
            else:
                res.append((lbl, int(rm)))

    # anything left over is seconds
    x = int(x)
    if(x == 1):
        res.append(("second", x))
    elif(x == 0):
        pass
    else:
        res.append(("seconds", x))

    return ", ".join(["%d %s" % (w[1], w[0]) for w in res])


def convertUnicode(elem):
    """Converts all unicode strings back into UTF-8 (str) so everything works.
        Call this function like:
            json.loads(s, object_hook=convertUnicode)"""
    if isinstance(elem, dict):
        return {convertUnicode(key): convertUnicode(value) for key, value in six.iteritems(elem)}
    elif isinstance(elem, list):
        return [convertUnicode(element) for element in elem]
    elif isinstance(elem, unicode):
        return elem.encode('utf-8')
    # DFW: Not sure if this has to be here, but deal with possible "null" MySQL strings
    elif(elem == 'null'):
        return None
    else:
        return elem


def urlEncodeMe(elem, safe=' '):
    """
        Converts any values that would cause JSON parsing to fail into URL percent encoding equivalents.
        This function can be used for any valid JSON type including str, dict, list.
        Returns:
            Same element properly encoded.
    """
    # What type am I?
    if isinstance(elem, dict):
        return {urlEncodeMe(key, safe): urlEncodeMe(value, safe) for key, value in six.iteritems(elem)}
    elif isinstance(elem, list):
        return [urlEncodeMe(element, safe) for element in elem]
    elif isinstance(elem, str):
        # Leave spaces alone, they are save to travel for JSON parsing
        return urllib.quote(elem, safe)
    else:
        return elem


def urlDecodeMe(elem):
    """
        Converts any values that would cause JSON parsing to fail into URL percent encoding equivalents.
        This function can be used for any valid JSON type including str, dict, list.
        Returns:
            Same element properly decoded.
    """
    # What type am I?
    if isinstance(elem, dict):
        return {urlDecodeMe(key): urlDecodeMe(value) for key, value in six.iteritems(elem)}
    elif isinstance(elem, list):
        return [urlDecodeMe(element) for element in elem]
    elif isinstance(elem, str):
        # Leave spaces alone, they are save to travel for JSON parsing
        return urllib.unquote(elem)
    else:
        return elem


def jsonPretty(j):
    """
        Returns a string of a JSON object in 'pretty print' format fully indented, and sorted.
    """
    return json.dumps(j, sort_keys=True, indent=4, separators=(',', ': '))


class dict2obj(object):

    def __init__(self, aDict=None, **kwargs):
        if(aDict is not None):
            aDict.update(kwargs)
        else:
            self.__dict__.update(kwargs)


def check(pkt, pktType, keyMatches=None, **valMatches):
    """This function takes an object that was expected to come from a packet (after it has been JSONized)
        and compares it against the arg requirements so you don't have to have 10 if() statements to look for keys in a dict, etc..

        Args:
            @pkt             : object to look at
            @pktType         : object type expected (dict, list, etc..)
            @keyMatches      : a list of minimum keys found in parent level of dict, expected to be an array
            @valMatches      : a dict of key:value pairs expected to be found in the parent level of dict
                              the value can be data (like 5) OR a type (like this value must be a @list@).
        Returns:
            None if everything matches, otherwise it returns a string as to why it failed."""
    # First check that the pkt type is equal to the input type
    if(type(pkt) is not pktType):
        return 'expected %s' % str(pktType)

    if(keyMatches):
        # Convert the keys to a set
        keyMatches = set(keyMatches)
        # The keyMatches is expected to be an array of the minimum keys we want to see in the pkt if the type is dict
        if(type(pkt) is dict):
            if(not keyMatches.issubset(pkt.keys())):
                return 'missing, "%s"' % ', '.join(list(keyMatches - set(pkt.keys())))
        else:
            return None

    # Finally for anything in the valMatches find those values
    if(valMatches):
        # Pull out the dict object from the "valMatches" key
        if('valMatches' in valMatches.keys()):
            matchObj = valMatches['valMatches']
        else:
            matchObj = valMatches

        for k, v in six.iteritems(matchObj):
            # Check for the key
            if(k not in pkt.keys()):
                return 'key missing "%s"' % k

            # See how we should be comparing it:
            if(type(v) is type):
                if(type(pkt[k]) is not v):
                    return 'key "%s", bad value type, "%s", expected "%s"' % (k, type(pkt[k]), v)

            else:
                # If key exists check value
                if(v != pkt[k]):
                    return 'key "%s", bad value data, "%s", expected "%s"' % (k, pkt[k], v)

    return None


def explode(pkt, *args):
    """This function takes a dict object and explodes it into the tuple requested.

        It returns None for any value it doesn't find.

        The only error it throws is if args is not defined.

        Example:
            pkt = {'a':0, 'b':1}
            0, 1, None = pdcomm.explode(pkt, 'a', 'b', 'c')
    """
    if not args:
        raise Exception("Required arguments not provided")

    # If there is an error make sure to return a tuple of the proper length
    if(not isinstance(pkt, dict)):
        return tuple([None] * len(args))

    # Now just step through the args and pop off everything from the packet
    # If a key is missing, the pkt.get(a, None) returns None rather than raising an Exception
    return tuple([pkt.get(a, None) for a in args])


class Timer(object):

    '''
    A timer object for simple benchmarking. 

    Usage:
        with Timer(key='Name of this test') as t:
            do.someCode(thatTakes=aWhile)

    Once the code finishes executing the time is output. 
    '''

    def __init__(self, key="", verbose=True):
        self.verbose = verbose
        self.key = key

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print(self.key + ' elapsed time: %f ms' % self.msecs)
