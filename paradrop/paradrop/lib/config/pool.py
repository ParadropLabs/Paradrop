import ipaddress
import itertools


class NetworkPool(object):
    def __init__(self, network, subnetSize=24):
        """
        network should be a string with network size in slash notation or as a
        netmask (e.g. 192.168.0.0/16 or 192.168.0.0/255.255.0.0).

        subnetSize specifies the size of subnets to create from the given
        network and should be larger than the prefix length of network (e.g.
        from 192.168.0.0/16 we can make 256 /24 subnets).
        """
        self.network = ipaddress.ip_network(unicode(network), strict=False)
        if subnetSize < self.network.prefixlen:
            raise Exception("Invalid subnetSize {} for network {}".format(
                subnetSize, network))
        self.subnets = itertools.cycle(self.network.subnets(
            new_prefix=subnetSize))
        self.numSubnets = 2 ** (subnetSize - self.network.prefixlen)
        self.used = set()

    def next(self):
        """
        Get an available subnet from the pool.

        Returns an ipaddress network object.  Raises an exception if no subnets
        are left.
        """
        if len(self.used) >= self.numSubnets:
            raise Exception("No subnets left in pool")

        # The for loop puts a limit on the number of iterations that we spend
        # looking for a free subnet.  Passing the check above should imply that
        # there is at least one available subnet, but we want to be extra
        # careful to avoid a busy loop.
        for i in range(self.numSubnets):
            subnet = self.subnets.next()
            if subnet not in self.used:
                self.used.add(subnet)
                return subnet

        # There is a bug if we hit this line.
        raise Exception("No subnets left in pool (BUG)")

    def release(self, subnet):
        """
        Release a previously claimed subnet.

        It may then be claimed by a subsequent call to nextSubnet.
        """
        if subnet in self.used:
            self.used.remove(subnet)


class NamePool(object):
    def __init__(self, length=4):
        self.length = length

        # Store next value for each (prefix, suffix) tuple.
        self.nextValue = dict()

        # List of freed names for each (prefix, suffix) tuple.
        self.freedNames = dict()

        # NOTE: Using base 16 for string representation.  It might be nice to
        # use a larger base ([0-9a-z] would allow base 36) for more possible
        # values for the same length.
        self.maxValue = (16 ** length) - 1

    def getNextValue(self, key):
        if key not in self.nextValue:
            self.nextValue[key] = 0

        nextValue = self.nextValue[key]

        # We cannot recover from this, but why is the system making so many
        # interfaces without ever releasing them?  It is most likely a bug.
        if nextValue > self.maxValue:
            raise Exception("Overflow occurred")

        self.nextValue[key] += 1

        return nextValue

    def next(self, prefix="", suffix=""):
        """
        Get a name from the pool.

        The name is constructed as prefix+X+suffix, where X is a fixed-length
        unique string (currently hexadecimal).
        """
        key = (prefix, suffix)
        if key in self.freedNames:
            if len(self.freedNames[key]) > 0:
                return self.freedNames[key].pop(0)

        nextValue = self.getNextValue(key)
        name = "{}{:0{}x}{}".format(prefix, nextValue, self.length, suffix)

        return name

    def release(self, name, prefix="", suffix=""):
        """
        Release a name allocated from the pool.

        NOTE: There is no error-checking.  Please be sure to release only
        things there were returned from the next() method, do not double
        release, etc.
        """
        key = (prefix, suffix)
        if key not in self.freedNames:
            self.freedNames[key] = list()

        self.freedNames[key].append(name)
