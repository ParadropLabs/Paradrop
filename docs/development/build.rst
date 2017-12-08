ParaDrop daemon development
====================================

ParaDrop repository includes a set of tools to make development as easy as possible.

Currently this system takes the form of a bash script that automates
installation and execution. This page outlines the steps required to manually
install the dependencies, build the package and install the package into
hardware/VMs.

We recommend using Ubuntu 16.04 LTS as the development environment for this
version of ParaDrop because we use `snapcraft <https://snapcraft.io/>`_ to
package and distribute the ParaDrop daemon.

You will only need to follow these instructions if you will be making changes
to the ParaDrop daemon.  Otherwise, you can use our pre-built ParaDrop snap or
disk image from `ParaDrop release <https://paradrop.org/release/>`_.

Building ParaDrop daemon
---------------------------

pdbuild.sh is the script we work with during the development.
It provides following commands:

- ``./pdbuild.sh setup`` installs development dependencies.

- ``./pdbuild.sh run`` executes the ParaDrop daemon locally in the development
  machine. It is useful for debugging.

- ``./pdbuild.sh build`` builds the snap package. Check `snapcraft
  documentation <https://snapcraft.io/docs/>`_ for detailed information about
  snap packages and snapcraft.

- ``./pdbuild.sh image`` builds the ubuntu core image that we can flash into SD
  card or SSD module of a ParaDrop router. It pre-installs the required snaps
  for us automatically, e.g. docker.

Installing ParaDrop into hardware/VMs
------------------------------------------

After the ParaDrop daemon snap is ready (paradrop-daemon_<version>_amd64.snap),
we can install it on a ParaDrop router. Check :doc:`../device/index` for
information about preparing a ParaDrop router.

Copy the paradrop snap to the router with ParaDrop image installed::

    scp paradrop-daemon-<version>_amd64.snap paradrop@<router ip>:

Then we can log in to a ParaDrop router::

    ssh paradrop@<router ip>

Install the dependent snaps in a ParaDrop router::

    snap install docker

Install the newly created ParaDrop daemon snap package::

    snap install --devmode paradrop-daemon-<version>_amd64.snap


Checking logs of ParaDrop daemon
----------------------------------

After install the ParaDrop daemon, we can use 'pdlog' to check the log of
ParaDrop daemon on the ParaDrop router::

    paradrop-daemon.pdlog -f


Building ParaDrop tools
------------------------

We have published the ParaDrop tools snap in the Ubuntu Snap Store. On the
development machine, we can install it with below command::

    snap install paradrop-tools

Get the manual of ParaDrop tools::

    paradrop-tools.pdtools --help

More detailed information about ParaDrop tools can be find in
:doc:`../application/index`. The git repository of ParaDrop includes the source
code of ParaDrop tools. Developers can build the latest version of ParaDrop
tools by running below command in the folder 'tools'::

    snapcraft
