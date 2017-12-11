Frequently Asked Questions
=============================

Please check here for issues or questions that commonly arise.

Issues with the hardware or operating system
--------------------------------------------

Issue 1: Docker fails to start after a reboot
"""""""""""""""""""""""""""""""""""""""""""""

This can happen if either the `docker.pid` file or the `docker-containerd.pid`
file was not properly cleaned up on system reboot, which causes the Docker
daemon to conclude that it is already running.

To fix this, remove the pid file on the router and reboot. ::

    sudo rm /var/snap/docker/current/run/docker.pid
    sudo rm /var/snap/docker/current/run/docker/libcontainerd/docker-containerd.pid
    sudo reboot

Occasionally Docker will crash and not restart properly even after a reboot.
We find that disabling and re-enabling the service helps in such cases. ::

    sudo snap disable docker
    sudo snap enable docker

Issue 2: WiFi devices are not detected after a reboot
"""""""""""""""""""""""""""""""""""""""""""""""""""""

Occasionally, when routers start up the WiFi devices are not detected properly.
When this happens the command ``iw dev`` will display nothing instead of the
expected devices.  This is usually remedied by rebooting.  A global setting to
reboot the router if WiFi devices are missing is available on the router
settings page.
