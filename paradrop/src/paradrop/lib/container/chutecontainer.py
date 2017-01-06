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
        client = docker.Client(base_url=self.docker_url, version='auto')
        try:
            info = client.inspect_container(self.name)
        except docker.errors.NotFound:
            raise ChuteNotFound("The chute could not be found.")

        return info['Id']

    def getPID(self):
        """
        Look up the PID of the container, if running.
        """
        client = docker.Client(base_url=self.docker_url, version='auto')
        try:
            info = client.inspect_container(self.name)
        except docker.errors.NotFound:
            raise ChuteNotFound("The chute could not be found.")

        if not info['State']['Running']:
            raise ChuteNotRunning("The chute is not running.")

        return info['State']['Pid']

    def getStatus(self):
        """
        Return the status of the container (running, exited, paused).
        """
        client = docker.Client(base_url=self.docker_url, version='auto')
        try:
            info = client.inspect_container(self.name)
        except docker.errors.NotFound:
            return "missing"

        return info['State']['Status']

    def isRunning(self):
        """
        Check if container is running.

        Returns True/False.
        """
        client = docker.Client(base_url=self.docker_url, version='auto')
        try:
            info = client.inspect_container(self.name)
        except docker.errors.NotFound:
            return False

        return info['State']['Running']
