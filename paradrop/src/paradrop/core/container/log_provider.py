'''
Provides messages from container logs (STDOUT and STDERR).
'''
import os
import signal
import docker
from multiprocessing import Process, Queue


def monitor_logs(chute_name, queue):
    """
    Iterate over log messages from a container and add them to the queue
    for consumption.  This function will block and wait for new messages
    from the container.  Use the queue to interface with async code.
    """
    client = docker.Client(base_url="unix://var/run/docker.sock", version='auto')
    output = client.logs(chute_name, stdout=True, stderr=True,
                         stream=True, timestamps=True, follow=True)
    for line in output:
        # I have grown to distrust Docker streaming functions.  It may
        # return a string; it may return an object.  If it is a string,
        # separate the timestamp portion from the rest of the message.
        if isinstance(line, basestring):
            parts = line.split(" ", 1)
            if len(parts) > 1:
                queue.put({
                    'timestamp': parts[0],
                    'message': parts[1].rstrip()
                })

            else:
                queue.put({
                    'message': line.rstrip()
                })
        else:
            queue.put(line)

class LogProvider(object):
    def __init__(self, chutename):
        self.chutename = chutename
        self.queue = Queue()
        self.listening = False

    def attach(self):
        """
        Start listening for log messages.

        Log messages in the queue will appear like the following:
        {
            'timestamp': '2017-01-30T15:46:23.009397536Z',
            'message': 'Something happened'
        }
        """
        if not self.listening:
            self.process = Process(target=monitor_logs, args=(self.chutename, self.queue))
            self.process.start()
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
            os.kill(self.process.pid, signal.SIGKILL)
            # self.process.terminate()
            # self.process.join()
            self.listening = False
