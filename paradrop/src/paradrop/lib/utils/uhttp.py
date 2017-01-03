import httplib
import socket


class UHTTPConnection(httplib.HTTPConnection):
    """
    Subclass of Python library HTTPConnection that uses a unix-domain socket.

    Source: http://7bits.nl/blog/posts/http-on-unix-sockets-with-python
    """

    def __init__(self, path):
        httplib.HTTPConnection.__init__(self, 'localhost')
        self.path = path

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock
