"""
The ProcessMonitor class ensures that a service is running and that its pid
file is consistent.

This addresses an issue we have had with Docker on Ubuntu Snappy, where its
pid file sometimes persists and prevents the service from starting.
"""
from __future__ import print_function

import glob
import os
import subprocess
import time

import psutil


class ProcessMonitor(object):
    # Specify allowed corrective actions, which we can change when running
    # locally to disable rebooting, for example.
    #
    # TODO: Implement a more general module for checking system health and
    # applying corrective action.
    allowedActions = set(["restart", "reboot"])

    def __init__(self, service, cmdstring=None, pidfile=None, action="restart"):
        """
        service: service name (used to restart it).
        cmdstring: string to look for in running command name (e.g. "docker")
        pidfile: None or path to look for pid file(s).
        Bash-style globbing is supported, e.g. "/var/snap/docker/*/run/docker.pid".
        action: "restart" the service or "reboot" the machine
        """
        self.service = service
        self.action = action

        if cmdstring is not None:
            self.cmdstring = cmdstring
        else:
            self.cmdstring = service

        if pidfile is not None:
            self.pidfiles = [ pidfile ]
        else:
            self.pidfiles = [
                "/var/snap/{service}/current/run/{service}.pid".format(service=service)]

    def check(self):
        """
        Check that the service is running and consistent with pid file(s).

        Returns True or False.
        """
        # Set of pids (strings) where the command string matches what we are
        # looking for.
        detected_pids = set()

        # Set of pids (strings) that are both running processes and found in
        # pid files.
        consistent_pids = set()

        # Search for running processes that match our command string.
        for proc in psutil.process_iter():
            try:
                if self.cmdstring in proc.name():
                    detected_pids.add(str(proc.pid))

            # We could also get psutil.ZombieProcess or
            # psutil.AccessDenied.  We want those to be logged.
            except psutil.NoSuchProcess:
                pass

        # Search for pid file(s) and check consistency.
        for pidfile in self.pidfiles:
            for path in glob.iglob(pidfile):
                with open(path, 'r') as source:
                    pid = source.read().strip()

                if pid in detected_pids:
                    consistent_pids.add(pid)
                else:
                    # Delete the stale pid file.
                    os.remove(path)

        return len(consistent_pids) > 0

    def restart(self):
        """
        Restart the service.
        """
        if self.action == "restart":
            cmd = ["snappy", "service", self.service, "restart"]
        else:
            cmd = ["shutdown", "-r", "now"]

        if self.action in ProcessMonitor.allowedActions:
            print("Running \"{}\" to fix {}".format(" ".join(cmd), self.service))
            return subprocess.call(cmd)
        else:
            print("Warning: would run \"{}\" to fix {}, but not allowed.".format(
                " ".join(cmd), self.service))

    def ensureReady(self, delay=5, tries=3):
        """
        Look through checking and restarting the service until it is ready or
        the maximum number of tries has been reached.

        delay: time delay (seconds) between retries.
        tries: maximum number of restart-wait-check cycles.
        """
        ready = self.check()
        if ready:
            return True

        for t in range(tries):
            time.sleep(delay)
            ready = self.check()
            if ready:
                return True
            else:
                self.restart()

        time.sleep(delay)
        return self.check()


dockerMonitor = ProcessMonitor("docker", action="reboot")
containerdMonitor = ProcessMonitor("docker-containerd",
        pidfile="/var/snap/docker/current/run/docker/libcontainerd/docker-containerd.pid",
        action="reboot")
