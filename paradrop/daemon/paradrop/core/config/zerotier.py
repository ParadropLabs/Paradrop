import os
import subprocess

from paradrop.base.output import out
from paradrop.lib.utils import datastruct


def execute(*args):
    result = subprocess.call(args)
    out.info("Command '{}' returned {}".format(" ".join(args), result))
    return result


def configure(update):
    hostConfig = update.new.getCache('hostConfig')

    enabled = datastruct.getValue(hostConfig, "zerotier.enabled", False)
    if enabled:
        if not os.path.exists("/snap/zerotier-one"):
            execute("snap", "install", "zerotier-one")

        # Make sure the service is running.
        execute("systemctl", "enable", "snap.zerotier-one.zerotier-one.service")
        execute("systemctl", "start", "snap.zerotier-one.zerotier-one.service")

        # The network-control interface is not automatically connected, so take
        # care of that.
        execute("snap", "connect", "zerotier-one:network-control")

        networks = datastruct.getValue(hostConfig, "zerotier.networks", [])
        for network in set(networks):
            execute("/snap/zerotier-one/current/usr/sbin/zerotier-cli",
                    "join", network)

    else:
        # Disable the zerotier service.
        execute("systemctl", "disable", "snap.zerotier-one.zerotier-one.service")
        execute("systemctl", "stop", "snap.zerotier-one.zerotier-one.service")


def getAddress():
    """
    Return the zerotier address for this device or None if unavailable.
    """
    try:
        with open("/var/snap/zerotier-one/common/identity.public", "r") as source:
            return source.read().strip()
    except:
        return None
