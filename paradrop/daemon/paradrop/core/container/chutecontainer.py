import docker

from paradrop.base.exceptions import ChuteNotFound, ChuteNotRunning


class ChuteContainer(object):
    """
    Class for accessing information about a chute's container.
    """
    def __init__(self, name, docker_url="unix://var/run/docker.sock"):
        self.name = name
        self.docker_url = docker_url

    def getID(self):
        """
        Look up the container ID as used by Docker.
        """
        info = self.inspect()

        return info['Id']

    def getIP(self):
        """
        Look up the IP address assigned to the container.
        """
        info = self.inspect()

        if not info['State']['Running']:
            raise ChuteNotRunning("The chute is not running.")

        return info['NetworkSettings']['IPAddress']

    def getPID(self):
        """
        Look up the PID of the container, if running.
        """
        info = self.inspect()

        if not info['State']['Running']:
            raise ChuteNotRunning("The chute is not running.")

        return info['State']['Pid']

    def getPortConfiguration(self, port, protocol="tcp"):
        """
        Look up network port configuration.  This tells us if a port in the
        host is bound to a port inside the container.

        Returns a list, typically with zero or one elements.

        Example:

            [{
                "HostIp": "0.0.0.0",
                "HostPort": "32768"
            }]
        """
        info = self.inspect()
        key = "{}/{}".format(port, protocol)
        try:
            return info['NetworkSettings']['Ports'][key]
        except:
            return []

    def getStatus(self):
        """
        Return the status of the container (running, exited, paused).

        Returns "missing" if the chute does not exist.
        """
        try:
            info = self.inspect()
            return info['State']['Status']
        except ChuteNotFound:
            return "missing"

    def inspect(self):
        """
        Return the full container status from Docker.
        """
        client = docker.APIClient(base_url=self.docker_url, version='auto')
        try:
            info = client.inspect_container(self.name)
            return info
        except docker.errors.NotFound:
            raise ChuteNotFound("The chute could not be found.")

    def isRunning(self):
        """
        Check if container is running.

        Returns True/False; returns False if the container does not exist.
        """
        try:
            info = self.inspect()
            return info['State']['Running']
        except ChuteNotFound:
            return False
