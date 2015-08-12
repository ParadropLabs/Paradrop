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
from twisted.cred import portal as twistedPortal
from twisted.internet.endpoints import SSL4ClientEndpoint
from twisted.internet.ssl import PrivateCertificate, Certificate, optionsForClientTLS

from zope.interface import implements
from pubsub import pub


from pdtools.lib.output import out


DEFAULT_PORT = 8016


############################################################
# Portal and Utility methods
############################################################

class Portal(twistedPortal.Portal):

    '''
    This is a portal for bi-directional communication between two parites. Both sides
    must have set up a portal in order to initiate communication. 

    Portals assign incoming connections to Realm objects based on the name assigned
    to the remote connection. Realms create avatars and return them across the wire. 

    Do not instantiate more than one portal-- don't instantiate it at all, actually.
    When serving or connecting, the global portal object in this class holds *all* 
    active connections.

    There are three instances where you may need to interact with the portal
        - initialization: set matchers and realms
        - access: find the connection with the given name or type
        - callback: assignable callbacks called when a new connection is made
            (Under consideration)
    '''

    def __init__(self):
        self.realms = {}
        self.host, self.port = 'localhost', DEFAULT_PORT

        self.certCa = None
        self.keyPrivate = None
        self.keyPublic = None

    def open(self, port=None, cert=None):
        '''
        Listen for connections on the given port. 
        '''
        port = port if port else self.port
        cert = cert if cert else self.certCa

        ca = Certificate.loadPEM(cert)
        myCertificate = PrivateCertificate.loadPEM(cert)

        SSL4ServerEndpoint(reactor, port, myCertificate.options(ca)).listen(RiffleServerFactory(self))

    @defer.inlineCallbacks
    def connect(self, host=None, port=None, cert=None, key=None):
        '''
        Connect to another portal.
        '''

        host = host if host else self.host
        port = port if port else self.port
        cert = cert if cert else self.certCa
        key = key if key else self.keyPrivate  # ???

        # the first term is the name the server is using in the cert (for now)
        ctx = optionsForClientTLS(u"pds.production", Certificate.loadPEM(cert), PrivateCertificate.loadPEM(key))

        factory = RiffleClientFactory()
        SSL4ClientEndpoint(reactor, host, port, ctx,).connect(factory)

        avatar = yield factory.login(self)

        defer.returnValue(Levy(avatar))

    def close(self):
        '''
        Close all connections in all realms.
        '''
        out.info("Portal closing all connections")
        for k, v in self.realms.iteritems():
            for c in v.connections:
                c.destroy()

    def addRealm(self, matcher, realm):
        '''
        Add a realm to this portal with its corresponding matcher. This can be done after
        the portal has been opened.

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

        for k, v in self.realms.iteritems():
            if k.match(credential):
                return v

        raise KeyError("No matcher was found to handle ", credential)

    def getRealm(self, matcher):
        '''
        Returns a realm based on a broad query for realm types.
        '''
        return self.realms[matcher]

    def login(self, credentials, mind):
        # print 'Login request from ' + credentials
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

    def connectionForName(self, credentials):
        '''
        Find the connection that has the given credentials.

        :param credentials: object to query for
        :type credentials: str.
        :return: the connection avatar or None
        '''

        # print 'Looking for connection with name:', credentials

        r = self.findRealm(credentials)
        # print r
        # print 'Connections:', len(r.connections)

        for c in r.connections:
            # print c

            if c.name == credentials:
                return c

        return None

portal = Portal()


def dumpRealms(portal=portal):
    s = 'Dumping all connections\n'

    for k, v in portal.realms.iteritems():
        s += '\tRealm: %s\n' % v.avatar.__name__

        for c in v.connections:
            s += '\t\t%s\n' % c.name

    print s


############################################################
# Realms, Avatars, and Levies
############################################################

class Realm:

    '''
    Wraps a type of avatar and all connections for that avatar type.

    Broadcasts connection changes using pubsub. To be notfied of new connections:
        pubsub.pub.subscribe(con, '[avatarName]Connected')
        pubsub.pub.unsubscribe(dis, '[avatarName]Disconnected')

    where 'dis' and 'con' are method references. Both take keyword arguments 'type'
    and 'realm'.
    '''
    implements(twistedPortal.IRealm)

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

        # print 'Attaching %s to %s' % (mind, avatar)
        avatar.attached(mind)

        # print avatar.remote

        self.connections.add(avatar)
        out.info('Connected: ' + avatar.name)
        pub.sendMessage('%sConnected' % self.avatar.__name__, avatar=avatar, realm=self)

        # yield mind.callRemote('echo', '')

        # deferred since initialization may require database operations
        # yield avatar.initialize()
        yield 1

        # move detached from the avatar to here?
        defer.returnValue((avatar, lambda a=avatar: a.detached(mind)))

    def attach(self, avatar, mind):
        '''
        Temp method. Performs the other half of the partial avatar method.

        Leaving the requestAvatar method is most likely a bad, bad idea.
        The more riffle diverges from PB the greater chance for bugs across the board.
        '''
        avatar.attached(mind)

        self.connections.add(avatar)
        out.info('Connected: ' + avatar.name)

    def requestPartialAvatar(self, avatarID):
        return self.avatar(avatarID, self)

    def requestPartialAvatar(self, avatarID):
        return self.avatar(avatarID, self)

    def connectionClosed(self, avatar):
        out.info('Disconnected: ' + str(avatar.name))
        pub.sendMessage('%sDisconnected' % self.avatar.__name__, avatar=avatar, realm=self)
        self.connections.remove(avatar)


class Levy(object):

    ''' Wraps a remote object reference to allow getattr magic '''

    def __init__(self, remote):
        self.remote = remote

    def __getattr__(self, item):
        def wrap(*args):
            return self.remote.callRemote(item, *args).addCallbacks(self.printValue, self.printError)

        return wrap

    # def __repr__(self):
    #     return 'Levy wrapping:\n\t' + repr(self.remote)

    def printValue(self, value):
        # print repr(value)
        return value

    def printError(self, error):
        out.warn('Default riffle error trap: ' + str(error))


class RifflePerspective(pb.Avatar):

    def __init__(self, name, realm):
        self.name = name
        self.realm = realm
        self.remote = None

    @defer.inlineCallbacks
    def initialize(self):
        '''
        An initialization method that may hit the database or perform other model
        related tasks needed to initialize this avatar. This method is meant to be subclassed. 

        NEVER make riffle calls here. There is no guarantee
        the other end of the connection is finished loading by the time this end of the connection
        is. Register for portal callbacks instead: this is a model and init method.
        '''
        yield

    def destroy(self):
        '''
        Dealloc and destroy. This is most likely called for Bad Reasons, 
        but for now its a catch all for all dealloc. 

        TODO: drop the connection (from twisted's perspective)
        '''
        pass

    @defer.inlineCallbacks
    def perspective_handshake(self):
        '''
        Utility method. Called when both ends of the connection have come online. 
        Only purpose is to call the initialize method.

        Note: malicious endpoints can easily call this repeatedly. Add a check 
        to ensure init is only called once. 
        '''
        # return self.initialize()
        yield self.initialize()

    def attached(self, mind):
        self.remote = Levy(mind)

    def detached(self, mind):
        self.destroy()
        self.remote = None
        self.realm.connectionClosed(self)

    def perspective_echo(self, arg):
        print 'Echo from %s: "%s"' % (self.name, arg)
        return arg


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

class _RiffleBroker(pb.Broker):

    def connectionLost(self, reason):
        '''
        This triggers many times, but the reason its here now is to 
        detect invalid certs. Without the print statement, the client isnt warned. This is a 
        todo item. 
        '''
        print 'Connection Lost!', reason
        return pb.Broker.connectionLost(self, reason)


class RiffleClientFactory(pb.PBClientFactory):

    protocol = _RiffleBroker

    @defer.inlineCallbacks
    def login(self, portal):
        # Have to add connection to the portal
        self.portal = portal

        # print 'Attempting to login!'
        # Returns a _RifflePortalWrapper remote reference
        root = yield self.getRootObject()
        # print 'Got the root object!'

        # Extract the name from credentials
        peerCertificate = Certificate.peerFromTransport(self._broker.transport)
        pdid = peerCertificate.getSubject().commonName.decode('utf-8')

        # Returns the server's avatar based on the client's interpretation
        # 'other' is the other end of the connection.
        other = self.portal.partialLogin(pdid)

        # Convert to remote referentiable for transmission
        referencibleOther = pb.AsReferenceable(other, "perspective")

        # Here is the problem. The login call triggers the init call, and that
        # starts the chain of riffle callbacks, but this object won't be back in time by then!

        # Avatar is the remotely described API object
        avatar = yield root.callRemote('login', referencibleOther)
        other.remote = Levy(avatar)

        # print 'Return Avatar: ' + str(avatar)
        # print 'Other Remote: ' + str(other)
        # print 'Not returned avatar: ' + str(a)
        # print ': ' + str(a.remote)
        # print 'Returned Mind: ' + str(other)

        # Signal we're done cleaning up
        # print 'Calling Handshake'

        # other.remote.callRemote('echo', 'boo')

        # This is absolutely not needed. The point of this method is to registers
        # the new connections with the portal, but we already have all the pieces.
        # a, b = yield self.portal.login(pdid, avatar)

        # tttteeeemmmpppppoooorrraaaarrryyy
        realm = self.portal.findRealm(pdid)
        realm.attach(other, avatar)
        # a, b = self.portal.

        # print 'Realm Object: ' + str(a)

        # Bit hacky, but should be cleaned up in a refactor
        # a.remote = avatar

        # other.remote = avatar

        avatar.callRemote('handshake')
        other.perspective_handshake()

        defer.returnValue(avatar)


class RiffleServerFactory(pb.PBServerFactory):

    protocol = _RiffleBroker

    def __init__(self, portal):
        pb.PBServerFactory.__init__(self, portal)
        # print 'Server factory started'
        self.root = _RifflePortalRoot(portal)


class _RifflePortalRoot(pb._PortalRoot):

    def rootObject(self, broker):
        # print 'Returning the root object!'
        return _RifflePortalWrapper(self.portal, broker)


class _RifflePortalWrapper(pb._PortalWrapper):

    @defer.inlineCallbacks
    def remote_login(self, client):
        # print 'Remote login!'
        peerCertificate = Certificate.peerFromTransport(self.broker.transport)
        pdid = peerCertificate.getSubject().commonName.decode('utf-8')

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

    def __init__(self, portal, broker):
        # print 'Root object initializing'
        self.portal = portal
        self.broker = broker

        self.broker.notifyOnDisconnect(disc)
        self.broker.notifyOnFail(fail)
        self.broker.notifyOnConnect(connect)

    def remote_loginAnonymous(self, mind):
        # print 'Remote login!'
        return None

# Do we need these? Who knows. Keeping them around for know, although
# these are a full level of abstraction below where we want to be, so be careful using them


def disc():
    # print 'CB: Disconnected'
    pass


def fail():
    # print 'CB: Failed'
    pass


def connect():
    # print 'CB: Connected'
    pass
