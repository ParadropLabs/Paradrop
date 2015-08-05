Quick Start
====================================

Paradrop includes a build system to make development as painless as possible.

This system, currently in the form of a script called ``pdbuild.sh`` in the root directory, handles both the paradrop system and applications that run on it (called chutes.)

Make sure to clone the `repository from github <https://github.com/ParadropLabs/Paradrop>`_  and set it as the active directory before getting started.


Paradrop
--------

This section details how to use the buildtools to compile and install paradrop on Ubuntu Snappy. 

Currently buildtools are configured only for installation on a virtual machine.

See buildtool help::

    ./pdbuild.sh 


Set up snappy
+++++++++++++

To set up snappy for local development::

    ./pdbuild.sh setup

Booting snappy image (this can take some time!)::

    ./pdbuild.sh up

Once running you can connect to the snappy virtual machine. By default, the username is ``ubuntu`` with password ``ubuntu``

Connecting to image::

    ./pdbuild.sh connect

Exiting image ssh session::

    exit

Terminating running snappy image::

    ./pdbuild.sh down


Install paradrop
+++++++++++++++++

Download and install dependancies::

    ./pdbuild.sh build

Run paradrop locally::

    ./pdbuild.sh run

To install paradrop on a snappy virtual machine you must make sure the virtual machine is running following the steps above. Specifically, make sure ``./pdbuild.sh up`` has been run.

Install paradrop on snappy::

    ./pdbuild.sh install