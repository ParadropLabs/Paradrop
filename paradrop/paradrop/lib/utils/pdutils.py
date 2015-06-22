###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
lib.utils.output.
Helper for formatting output from Paradrop.
"""

import time

timeflt = lambda: time.time()
timeint = lambda: int(time.time())
timestr = lambda x=None: time.asctime(time.localtime(x)) if x else time.asctime()

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
    
    return ", ".join(["%d %s" % (x[1], x[0]) for x in res])

def convertUnicode(elem):
    """Converts all unicode strings back into UTF-8 (str) so everything works.
        Call this function like:
            json.loads(s, object_hook=convertUnicode)"""
    if isinstance(elem, dict):
        return {convertUnicode(key): convertUnicode(value) for key, value in elem.iteritems()}
    elif isinstance(elem, list):
        return [convertUnicode(element) for element in elem]
    elif isinstance(elem, unicode):
        return elem.encode('utf-8')
    #DFW: Not sure if this has to be here, but deal with possible "null" MySQL strings
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
        return {urlEncodeMe(key, safe): urlEncodeMe(value, safe) for key, value in elem.iteritems()}
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
        return {urlDecodeMe(key): urlDecodeMe(value) for key, value in elem.iteritems()}
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

def json2str(j, safe=' '):
    """
        Properly converts and encodes all data related to the JSON object into a string format
        that can be transmitted through a network and stored properly in a database.
        Arguments:
            @j    : json to be converted
            @safe : optional, string of chars to pass to urlEncodeMe that are declared safe (don't encode)
    """
    return json.dumps(urlEncodeMe(j, safe), separators=(',', ':'))

def str2json(s):
    t = json.loads(s, object_hook=convertUnicode)
    # If t is a list, object_hook was never called (by design of json.loads)
    # deal with that situation here
    if(isinstance(t, list)):
        t = [convertUnicode(i) for i in t]
    # Make sure to still decode any strings
    return urlDecodeMe(t)
