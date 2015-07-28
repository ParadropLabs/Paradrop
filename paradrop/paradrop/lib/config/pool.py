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
