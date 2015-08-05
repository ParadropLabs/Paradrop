import ipaddress
import itertools

from pdtools.lib.output import out


class ResourcePool(object):
    def __init__(self, values, numValues):
        """
        Initialize resource pool.

        values - must be iterable, such as a list or generator
        numValues - number of values, since len need not be defined
        """
        self.values = values
        self.numValues = numValues

        self.cycle = itertools.cycle(values)

        self.recentlyReleased = list()
        self.used = set()

    def next(self):
        if len(self.used) >= self.numValues:
            raise Exception("No items left in pool")

        while len(self.recentlyReleased) > 0:
            item = self.recentlyReleased.pop(0)
            if item not in self.used:
                out.info("Claiming recently released {} from pool {}\n".format(
                         str(item), self.__class__.__name__))
                self.used.add(item)
                return item

        # The for loop puts a limit on the number of iterations that we spend
        # looking for a free subnet.  Passing the check above should imply that
        # there is at least one available item, but we want to be extra
        # careful to avoid a busy loop.
        for i in range(self.numValues):
            item = self.cycle.next()
            if item not in self.used:
                out.info("Claiming new item {} from pool {}\n".format(
                         str(item), self.__class__.__name__))
                self.used.add(item)
                return item

        # There is a bug if we hit this line.
        raise Exception("No items left in pool (BUG)")

    def release(self, item):
        out.info("Trying to release {} from pool {}\n".format(str(item),
                 self.__class__.__name__))
        if item in self.used:
            self.used.remove(item)
            self.recentlyReleased.append(item)
        else:
            raise Exception("Trying to release unreserved item")

    def reserve(self, item, strict=True):
        """
        Mark item as used.

        If strict is True, raises an exception if the item is already used.
        """
        out.info("Trying to reserve {} from pool {}\n".format(str(item),
                 self.__class__.__name__))
        if item in self.used:
            if strict:
                raise Exception("Trying to reserve a used item")
        else:
            self.used.add(item)


class NetworkPool(ResourcePool):
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

        subnets = self.network.subnets(new_prefix=subnetSize)
        numSubnets = 2 ** (subnetSize - self.network.prefixlen)

        super(NetworkPool, self).__init__(subnets, numSubnets)


class NumericPool(ResourcePool):
    def __init__(self, digits=4):
        self.digits = digits

        # NOTE: Using base 16 for string representation.  It might be nice to
        # use a larger base ([0-9a-z] would allow base 36) for more possible
        # values for the same length.
        numNames = 16 ** digits
        values = range(numNames)

        super(NumericPool, self).__init__(values, numNames)
