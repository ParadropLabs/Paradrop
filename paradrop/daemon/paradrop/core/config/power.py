import subprocess


def reboot(update):
    """
    Reboot the node.
    """
    cmd = ["shutdown", "-r", "+1"]
    result = subprocess.call(cmd)
    if result == 0:
        update.progress("Rebooting in 60 seconds.")
    else:
        raise Exception("shutdown command failed, returned {}".format(result))


def shutdown(update):
    """
    Power down the node.
    """
    cmd = ["shutdown", "-h", "+1"]
    result = subprocess.call(cmd)
    if result == 0:
        update.progress("Halting in 60 seconds.")
    else:
        raise Exception("shutdown command failed, returned {}".format(result))
