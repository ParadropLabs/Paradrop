Build System
====================================

Paradrop includes a set of build tools to make development as easy
as possible.

Currently this system takes the form of a bash script that automates
installation and execution, but in time this may evolve into a published
python package. This page outlines the steps required to manually build
the components required to develop with paradrop.

Components in the build process:

- `Installing and running Ubuntu Snappy`_
- `Building paradrop`_
- `Installing paradrop`_
- `Creating chutes`_

We recommend using Ubuntu 14.04 as the build environment for this version
of Paradrop.  Ubuntu 16.04 will not work because the snappy development
tools have changed.  The next release of Paradrop will use the new tools.

You will only need to follow these instructions if you will be making
changes to the Paradrop instance tools.  Otherwise, you can
use our pre-built Paradrop disk image.  Please visit the
:doc:`../chutes/gettingstarted` page.

Installing and running Ubuntu Snappy
------------------------------------

`Snappy <https://developer.ubuntu.com/en/snappy/>`_ is an Ubuntu release
focusing on low-overhead for a large set of platforms. These instructions
are for getting a Snappy instance up and running using 'kvm'.

Download and unzip a snappy image::

    wget http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz
    unxz ubuntu-15.04-snappy-amd64-generic.img.xz

Launch the snappy image using kvm::

    kvm -m 512 -redir :8090::80 -redir :8022::22 ubuntu-15.04-snappy-amd64-generic.img

Connect to local instance using ssh::

    ssh -p 8022 ubuntu@localhost

Building paradrop
--------------------

Snappy is a closed system (by design!). Arbitrary program installation
is not allowed, so to allow paradrop access to the wide world of ``pypi``
the build system relies on two tools.

- ``virtualenv`` is a tool that creates encapsulated environments in
  which python packages can be installed.
- ``pex`` can compress python packages into a zip file that can be
  executed by any python interpreter.
- ``snappy`` is a tool for building snap packages.  *Note:* Ubuntu 16.04
  uses snapcraft instead, which produces incompatible packages.

First, set `DEV_MACHINE_IP=paradrop.org` in pdbuild.conf.  The build
script will refuse to run if this variable is not set.

Install the necessary development tools::

    ./pdbuild.sh setup

Build the Paradrop snap package::

    ./pdbuild.sh build

Installing paradrop
--------------------

Install dependencies on the virtual machine::

    ./pdbuild.sh install_deps

Install the newly created Paradrop snap package::

    ./pdbuild.sh install_dev

