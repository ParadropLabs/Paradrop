'''
Naming and permissions.

All objects are identified by a human-readable UUID, which is a domain-style
identifier. These are PDIDs.

All PDID's are prefaced with a top-level name. This currently serves no purpose
other than to make it obvious when a PDID appears, but could be used later
for alternative namespacing (development mode, 3rd party servers, etc).

There is exactly one special case when it comes to PDIDs in order to deal with
a conflict: specifying a chute "in the store." A user's top level namespace
is always followed by either a router name: pd.damouse.routerName OR a
chute namespace declaration: pd.damouse.chutes.chuteName. Queries for
pd.damouse.chuteName will be oppertunistically queried, but collisions must
ask the user to resolve the conflict.

Examples:
    User 'damouse':
        pd.damouse

    Chute 'netflix':
        pd.damouse.chutes.netflix

    Router 'aardvark':
        pd.damouse.aardvark

    Chute instance 'netflix':
        pd.damouse.aardvark.netflix


Full ids cannot have namespace collisions by definition. This has a few consequences:
    Chute names must be unique
    Owned router names must be unique

TODO:
    return constant values from idValid instead of strings
    Subdomaining should not require enumeration, fix.

Note that Groups, Organizations, and Chute Versions were previously pd.namespace objects, but
they do not offer enough flexibility-- these are now metatdata fields (but this could change)
'''

from pdtools.lib.exceptions import *

from enum import Enum
import re


###################################################
# Precompiled matchers for performance
###################################################

# A basic, valid name for anything
n = r'[a-zA-Z0-9]{3,32}'
basic = re.compile(r'pd\.%s' % n)

NameTypes = Enum('NameTypes', 'user, chute, router, instance, server')

matchers = {
    NameTypes.user: re.compile(r'^pd\.%s$' % n),
    NameTypes.chute: re.compile(r'^pd\.%s\.chutes\.%s$' % (n, n)),
    NameTypes.router: re.compile(r'^pd\.%s\.%s$' % (n, n)),
    NameTypes.instance: re.compile(r'^pd\.%s\.%s\.%s$' % (n, n, n)),
    NameTypes.server: re.compile(r'^pds.production$')
}


###################################################
# Formatting and Construction
###################################################

def idForUser(username):
    return 'pd.' + username


def idForChute(username, chuteName):
    return idForUser(username) + '.chutes.' + chuteName


def idForRouter(username, routerName):
    return idForUser(username) + '.' + routerName


def idForInstance(username, routerName, chuteName):
    return idForRouter(username, routerName) + '.' + chuteName


###################################################
# Validation
###################################################

def idValid(pdid):
    '''
    Checks any pdid for valid structure, but does not check that it is a
    valid reference (in other words it does not check the database)

    :returns: NameType specifying the type of this pdid
    '''

    if not basic.match(pdid):
        raise PdidError("Indeterminate PDID.")

    for k, v in matchers.iteritems():
        if v.match(pdid):
            return k

    # Might want to make this a little more specfic
    raise PdidError("Indeterminate PDID. Names must be between 3 and 32 characters.")
