Known Issues
========================

Please check here for issues during setup.

Issues using pdbuild.sh
---------------------------

These issues are related to the *Instance Tools* found on github.

Issue 1: ``pdbuild.sh install`` fails
""""""""""""""""""""""""""""""""""""""""
Docker snap is missing inside of virtual router, run ``pdbuild.sh install_deps``::

    issues while running ssh command: Installing /tmp/paradrop_0.1.0_all.snap
    2015/08/11 21:22:57 Signature check failed, but installing anyway as requested
    /tmp/paradrop_0.1.0_all.snap failed to install: missing frameworks: docker

Issue 2: ``pdbuild.sh install`` fails
"""""""""""""""""""""""""""""""""""""""
.. TODO: remove this once pdconfd is fixed

This is a known issue for the Paradrop team, if you get this please email us at developers@paradrop.io::

    Installing paradrop_0.1.0_all.snap from local environment

    issues while running ssh command: Installing /tmp/paradrop_0.1.0_all.snap
    2015/08/11 21:29:48 Signature check failed, but installing anyway as requested
    /tmp/paradrop_0.1.0_all.snap failed to install: [start paradrop_pdconfd_0.1.0.service]
    failed with exit status 1: Job for paradrop_pdconfd_0.1.0.service failed.
    See "systemctl status paradrop_pdconfd_0.1.0.service" and "journalctl -xe" for details.

Issue 3: ``pdbuild.sh up`` fails
"""""""""""""""""""""""""""""""""""

This is very common and will happen if you delete your VM and setup a
fresh one, which will have a different key.  The solution is simple and
is stated in the error message.  Follow the instructions to remove the
key from your known_hosts file. ::

    Failed to setup keys: failed to setup keys: issues while running ssh command:
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
    Someone could be eavesdropping on you right now (man-in-the-middle attack)!
    It is also possible that a host key has just been changed.
    The fingerprint for the ECDSA key sent by the remote host is
    e6:ec:b1:93:7d:91:84:50:19:36:14:8e:ce:ef:6a:0b.
    Please contact your system administrator.


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
