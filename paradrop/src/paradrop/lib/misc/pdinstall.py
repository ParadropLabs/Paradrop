import json
import socket


SOCKET_ADDRESS = "/var/run/pdinstall.sock"


def sendCommand(command, data):
    """
    Send a command to the pdinstall service.

    Commands:
    install - Install snaps from a file path or http(s) URL.
        Required data fields:
        sources - List with at least one snap file path or URL.  The snaps
                  are installed in order until one succeeds or all fail.

    Returns True/False for success.  Currently, we cannot check whether the
    call succeeded, only whether it was delived.  A return value of False means
    we could not deliver the command to pdinstall.
    """
    data['command'] = command

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(SOCKET_ADDRESS)
        sock.send(json.dumps(data))
        return True
    except:
        return False
    finally:
        sock.close()
