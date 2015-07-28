'''
Riffle- "A segment of stream where the flow is shallower and more turbulent."

Riffle is concerned with abstracting persistent TCP/TLS connections. Exhaustively, 
riffle is a deferred RPC protocol over TLS based on twisted.pb.PerspectiveBroker that uses Avatars 
automagically created from self-signed SSL keys. 

Conceptually, there are three important parts:
    - interacting with remote clients through RPC 
    - managing persistent connections
    - connecting or listening for Riffle connections

More to follow. 
'''

from twisted.python.filepath import FilePath
from twisted.internet.endpoints import SSL4ServerEndpoint
from twisted.internet.task import react
from twisted.internet import reactor
from twisted.internet import defer
from twisted.spread import pb
from twisted.cred import portal

from zope.interface import implements

from twisted.internet.endpoints import SSL4ClientEndpoint
from twisted.internet.ssl import PrivateCertificate, Certificate, optionsForClientTLS


class Riffle(object):

    def __init__(self, host, port, secure=True):
        '''
        This is not a Twisted style 'protocol', its a wrapper around a modified PB. 
        The Riffle object makes creating new riffle sessions easier. 

        :param host: the hostname to connect/listen to 
        :type host: str.
        :param port: port to connect/listen to
        :type port: int
        :param secure: should riffle connect over TLS or not? This is a temporary thing
        :type secure: bool.
        '''
        self.host, self.port = host, port
        self.secure = secure

    def _serverContext(self, pem):
        ca = Certificate.loadPEM(pem)
        myCertificate = PrivateCertificate.loadPEM(pem)

        return SSL4ServerEndpoint(reactor, self.port, myCertificate.options(ca))

    def _clientContext(self, caCert, pkey):
        ctx = optionsForClientTLS(u"pds.production", Certificate.loadPEM(caCert), PrivateCertificate.loadPEM(pkey))
        return SSL4ClientEndpoint(reactor, self.host, self.port, ctx,)

    def serve(self, keypath):
        serverEndpoint = self._serverContext(keypath)
        serverEndpoint.listen(RiffleServerFactory(portal))

    @defer.inlineCallbacks
    def connect(self, caCert, keys):
        clientEndpoint = self._clientContext(caCert, keys)

        factory = RiffleClientFactory()
        clientEndpoint.connect(factory)

        avatar = yield factory.login(portal)

        defer.returnValue(Levy(avatar))


############################################################
# Realms, Portals, and Wrappers
# These classes are not meant to be subclassed
############################################################

class Portal(portal.Portal):

    '''
    Bi-directional portal. Stores connections and is responsible for allocating
    new connections with appropriate avatars.

    Currently takes a dict, but this isn't ideal
    '''

    def __init__(self):
        self.realms = {}

    def addRealm(self, matcher, realm):
        '''
        Add a realm to this portal with its corresponding matcher. This must be done
        before the server is started or connections are made, else requesting peers
        may fail to connect. 

        :param realm: the realm object that will handle the incoming connections
        :type realm: riffle.Realm
        :param matcher: an re matcher object that tests presented domain names for incoming clients
        :type matcher: re.matcher
        '''
        self.realms[matcher] = realm

    def findRealm(self, credential):
        '''
        Find the appropriate realm for the given credential. Matches are found using
        re filters. 
        '''
        # print self.realms
        # return self.realms[credential]

        for k, v in self.realms.iteritems():
            if k.match(credential):
                return v

        raise KeyError("No matcher was found to handle ", credential)

    def login(self, credentials, mind):
        print str(credentials) + ' attempting to login'
        target = self.findRealm(credentials)
        return target.requestAvatar(credentials, mind)

    def partialLogin(self, credentials):
        '''
        Clients send servers their representations before the server gives the client 
        its 'mind' object. This call returns the correct representation for the server
        *without* the mind object. Does not add the avatar to a realm. 
        '''
        target = self.findRealm(credentials)
        return target.requestPartialAvatar(credentials)


class Realm:

    '''
    Wraps a type of avatar and all connections for that avatar type
    '''
    implements(portal.IRealm)

    def __init__(self, avatar):
        self.avatar = avatar
        self.connections = set()

    @defer.inlineCallbacks
    def requestAvatar(self, avatarID, mind):
        '''
        Returns an instance of the appropriate avatar. Asks the avatar to perform 
        any needed initialization (which should be a deferred)
        '''
        avatar = self.avatar(avatarID, self)
        avatar.attached(mind)
        yield avatar.initialize()

        self.connections.add(avatar)

        # move detached from the avatar to here?
        defer.returnValue((avatar, lambda a=avatar: a.detached(mind)))

    def requestPartialAvatar(self, avatarID):
        return self.avatar(avatarID, self)

    def connectionClosed(self, avatar):
        ''' An avatar disconnected '''
        print 'Connection lost'
        self.connections.remove(avatar)


class Levy(object):

    ''' Wraps a remote object reference to allow __getattr__ magic '''

    def __init__(self, remote):
        self.remote = remote

    def __getattr__(self, item):
        def wrap(*args):
            return self.remote.callRemote(item, *args).addCallbacks(self.printValue, self.printError)

        return wrap

    def printValue(self, value):
        print repr(value)
        return value

    def printError(self, error):
        print 'Error Callback'
        print 'error', error


############################################################
# Avatar, Referencable, and Viewable base classes
############################################################

class RifflePerspective(pb.Avatar):

    def __init__(self, name, realm):
        self.name = name
        self.realm = realm

    @defer.inlineCallbacks
    def initialize(self):
        '''
        An initialization method that may hit the database or perform other model
        related tasks needed to initialize this avatar. This method is meant to be subclassed. 
        '''
        yield 1
        defer.returnValue(None)

    def attached(self, mind):
        self.remote = mind

    def detached(self, mind):
        self.remote = None
        self.realm.connectionClosed(self)


class RiffleReferencable(pb.Referenceable):

    def __init__(self, name, realm):
        self.name = name

    def connected(self, perspective):
        ''' Called when a remote user gains access to this object. Must save a reference '''
        self.perspective = perspective


class RiffleViewable(pb.Viewable):

    def view_doFoo(self, perspective, arg1, arg2):
        print 'Do Foo!', perspective, arg1, arg2
        return 'Done'


############################################################
# Perspective Broker Monkey Patches
############################################################

class RiffleClientFactory(pb.PBClientFactory):

    @defer.inlineCallbacks
    def login(self, portal):
        # Have to add connection to the portal
        self.portal = portal

        print 'Requesting root object'
        root = yield self.getRootObject()
        print 'Got root:', root

        peerCertificate = Certificate.peerFromTransport(self._broker.transport)
        pdid = peerCertificate.getSubject().commonName.decode('utf-8')

        # Returns the server's avatar based on the client's interpretation
        client = self.portal.partialLogin(pdid)
        client = pb.AsReferenceable(client, "perspective")

        avatar = yield root.callRemote('login', client)

        self.portal.login(pdid, avatar)

        defer.returnValue(avatar)


class RiffleServerFactory(pb.PBServerFactory):

    def __init__(self, portal):
        pb.PBServerFactory.__init__(self, portal)
        self.root = _RifflePortalRoot(portal)


class _RifflePortalRoot(pb._PortalRoot):

    def rootObject(self, broker):
        return _RifflePortalWrapper(self.portal, broker)


class _RifflePortalWrapper(pb._PortalWrapper):

    @defer.inlineCallbacks
    def remote_login(self, client):
        print 'Received a request for a remote login'

        peerCertificate = Certificate.peerFromTransport(self.broker.transport)
        pdid = peerCertificate.getSubject().commonName.decode('utf-8')
        print 'Got pdid', pdid

        avatar, logout = yield self.portal.login(pdid, client)
        avatar = pb.AsReferenceable(avatar, "perspective")

        # Formerly in _cbLogin, moved here to make the deferred chain cleaner
        puid = avatar.processUniqueID()

        # only call logout once, whether the connection is dropped (disconnect)
        # or a logout occurs (cleanup), and be careful to drop the reference to
        # it in either case
        logout = [logout]

        def maybeLogout():
            if not logout:
                return
            fn = logout[0]
            del logout[0]
            fn()

        self.broker._localCleanup[puid] = maybeLogout
        self.broker.notifyOnDisconnect(maybeLogout)

        defer.returnValue(avatar)


############################################################
# Utility Methods
############################################################

def dumpRealms(portal):
    for k, v in portal.realms.iteritems():

        for c in v.connections:
            print '\t', c

# Globally exposed portal object. Anyone using this class is going to need a portal,
# hence why its exposed

portal = Portal()
