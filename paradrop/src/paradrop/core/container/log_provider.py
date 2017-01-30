'''
Provides messages from container logs (STDOUT and STDERR).
'''

import docker
from twisted.internet import reactor, threads
from twisted.internet.defer import DeferredQueue


class LogProvider(object):
    def __init__(self, chutename):
        self.chutename = chutename
        self.queue = DeferredQueue()
        self.listening = False

    def attach(self):
        """
        Start listening for log messages.

        Returns a DeferredQueue that can be used by an async consumer.

        Log messages in the queue will appear like the following:
        {
            'timestamp': '2017-01-30T15:46:23.009397536Z',
            'message': 'Something happened'
        }
        """
        reactor.callInThread(self.__follow)
        self.listening = True
        return self.queue

    def detach(self):
        """
        Stop listening for log messages.

        After this is called, no additional messages will be added to the
        queue.
        """
        self.listening = False

    def __follow(self):
        """
        Iterate over log messages from a container and add them to the queue
        for consumption.  This function will block and wait for new messages
        from the container.  Use the queue to interface with async code.
        """
        client = docker.Client(base_url="unix://var/run/docker.sock", version='auto')
        output = client.logs(self.chutename, stdout=True, stderr=True,
                stream=True, timestamps=True, follow=True)
        for line in output:
            if not self.listening:
                break

            # I have grown to distrust Docker streaming functions.  It may
            # return a string; it may return an object.  If it is a string,
            # separate the timestamp portion from the rest of the message.
            if isinstance(line, basestring):
                parts = line.split(" ", 1)
                if len(parts) > 1:
                    self.queue.put({
                        'timestamp': parts[0],
                        'message': parts[1].rstrip()
                    })

                else:
                    self.queue.put({
                        'message': line.rstrip()
                    })
            else:
                self.queue.put(line)
