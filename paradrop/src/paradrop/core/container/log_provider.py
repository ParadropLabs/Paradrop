'''
Provides messages from container logs (STDOUT and STDERR).
'''

import docker
from twisted.internet import reactor, threads
from twisted.internet.defer import DeferredQueue


class LogProvider(object):
    def __init__(self, chutename):
        self.chutename = chutename

    def attach(self):
        queue = DeferredQueue()
        reactor.callInThread(self.__follow(queue))
        return queue

    def __follow(self, queue):
        client = docker.Client(base_url="unix://var/run/docker.sock", version='auto')
        output = client.logs(self.chutename, stdout=True, stderr=True,
                stream=True, timestamps=True, follow=True)
        for line in output:
            queue.put(line)
