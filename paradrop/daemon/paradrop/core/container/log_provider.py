'''
Provides messages from container logs (STDOUT and STDERR).
'''
import os
import signal

import docker
import six

from multiprocessing import Process, Queue


def monitor_logs(service_name, container_name, queue, tail=200):
    """
    Iterate over log messages from a container and add them to the queue
    for consumption.  This function will block and wait for new messages
    from the container.  Use the queue to interface with async code.

    tail: number of lines to retrieve from log history; the string "all"
    is also valid, but highly discouraged for performance reasons.
    """
    client = docker.DockerClient(base_url="unix://var/run/docker.sock", version='auto')
    container = client.containers.get(container_name)
    output = container.logs(stdout=True, stderr=True,
                            stream=True, timestamps=True, follow=True,
                            tail=tail)
    for line in output:
        # I have grown to distrust Docker streaming functions.  It may
        # return a string; it may return an object.  If it is a string,
        # separate the timestamp portion from the rest of the message.
        if isinstance(line, six.string_types):
            parts = line.split(" ", 1)
            if len(parts) > 1:
                queue.put({
                    'service': service_name,
                    'timestamp': parts[0],
                    'message': parts[1].rstrip()
                })

            else:
                queue.put({
                    'service': service_name,
                    'message': line.rstrip()
                })
        elif isinstance(line, dict):
            line['service'] = service_name
            queue.put(line)

class LogProvider(object):
    def __init__(self, chute):
        self.chute = chute
        self.queue = Queue()
        self.listening = False
        self.processes = []

    def attach(self):
        """
        Start listening for log messages.

        Log messages in the queue will appear like the following:
        {
            'service': 'main',
            'timestamp': '2017-01-30T15:46:23.009397536Z',
            'message': 'Something happened'
        }
        """
        if not self.listening:
            for service in self.chute.get_services():
                process = Process(target=monitor_logs,
                        args=(service.name, service.get_container_name(), self.queue))
                process.start()
                self.processes.append(process)
            self.listening = True

    def get_logs(self):
        logs = []
        while not self.queue.empty():
            msg = self.queue.get()
            logs.append(msg)
        return logs

    def detach(self):
        """
        Stop listening for log messages.

        After this is called, no additional messages will be added to the
        queue.
        """
        if self.listening:
            # We have to kill the process explicitly with SIGKILL,
            # terminate() function does not work here.
            for process in self.processes:
                os.kill(process.pid, signal.SIGKILL)

            self.processes = []
            self.listening = False
