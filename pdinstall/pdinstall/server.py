import json
import os
import socket


MAX_MSG_SIZE = 4096


class CommandServer(object):
    def __init__(self, address):
        self.address = address
        self.handlers = dict()

    def addHandler(self, command, handler):
        """
        Add a handler function for a command.

        The handler must take one argument, a dictionary containing the request
        data.
        """
        if command not in self.handlers:
            self.handlers[command] = list()
        self.handlers[command].append(handler)

    def run(self):
        """
        Enter the main loop.
        """
        try:
            os.remove(self.address)
        except OSError as err:
            pass

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.address)
        sock.listen(socket.SOMAXCONN)

        self.running = True
        while self.running:
            conn, address = sock.accept()
            try:
                data = conn.recv(MAX_MSG_SIZE)
                request = json.loads(data)
                cmd = request['command']
                if cmd in self.handlers:
                    for callback in self.handlers[cmd]:
                        callback(request)
            except Exception as e:
                print("Caught exception {}".format(e))
                pass
            finally:
                conn.close()

        sock.close()
        os.remove(self.address)
