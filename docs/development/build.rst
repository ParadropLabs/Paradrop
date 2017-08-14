Build System
====================================

Paradrop includes a set of build tools to make development as easy
as possible.

Currently this system takes the form of a bash script that automates
installation and execution, but in time this may evolve into a published
python package. This page outlines the steps required to manually build
the components required to develop with paradrop.

Components in the build process:
- `Building paradrop daemon`_
- `Installing paradrop into hardware/VM`_
- `Building pdtools`_
- `Configuring paradrop router through web portal`_

We recommend using Ubuntu 14.04 as the build environment for this version
of Paradrop.  Ubuntu 16.04 will not work because the snappy development
tools have changed.  The next release of Paradrop will use the new tools.

You will only need to follow these instructions if you will be making
changes to the Paradrop instance tools.  Otherwise, you can
use our pre-built Paradrop disk image.  Please visit the
:doc:`../chutes/gettingstarted` page.

Building paradrop daemon
---------------------------

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

Installing paradrop into hardware/VM
------------------------------------------

Install dependencies on the virtual machine::

    ./pdbuild.sh install_deps

Install the newly created Paradrop snap package::

    ./pdbuild.sh install_dev


Configuring paradrop router through web portal
------------------------------------------------
TODO
