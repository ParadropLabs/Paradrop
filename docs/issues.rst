Known Issues
========================

Please check here for issues during setup.

Issues with the hardware or operating system
--------------------------------------------

Issue 1: Docker fails to start after a reboot
"""""""""""""""""""""""""""""""""""""""""""""

This can happen if the 'docker.pid' file was not properly cleaned up,
which causes the docker daemon to conclude that it is already running.

To fix this, remove the pid file on the router and reboot. ::

    sudo rm /var/lib/apps/docker/1.11.2/run/docker.pid
    sudo reboot

Issue 2: WiFi devices are not detected after a reboot
"""""""""""""""""""""""""""""""""""""""""""""""""""""

Occasionally, when routers start up the WiFi devices are not detected
properly.  When this happens the command ``iw dev`` will display nothing
instead of the expected devices.  This is usually remedied by rebooting.
