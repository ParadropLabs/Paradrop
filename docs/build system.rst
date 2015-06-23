Build System
====================================

Paradrop includes a set of build tools to make development as easy as possible. 

Currently this system takes the form of a bash script that automates installation and execution, but 
in time this may evolve into a published python package. This page outlines the steps required to 
manually build the components required to develop with paradrop.

Components in the build process:

- `Installing and running Ubuntu Snappy`_
- `Building paradrop`_
- `Installing paradrop`_
- `Creating chutes`_

Installing and running Ubuntu Snappy
------------------------------------

[Snappy](https://developer.ubuntu.com/en/snappy/) is an Ubuntu release focusing on low-overhead for a large set of platforms. These instructions are for getting a Snappy instance up and running using 'kvm'. 

Download and unzip a snappy image::

    wget http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz
    unxz ubuntu-15.04-snappy-amd64-generic.img.xz


Launch the snappy image using kvm::

    kvm -m 512 -redir :8090::80 -redir :8022::22 ubuntu-15.04-snappy-amd64-generic.img


Connect to local instance using ssh::

    ssh -p 8022 ubuntu@localhost


Building paradrop
--------------------

Snappy is a closed system (by design!). Arbitrary program installation is not allowed, so to allow paradrop access to the wide world of ``pypi`` the build system relies on two tools. 

- ``virtualenv`` is a tool that creates encapsulated environments in which python packages can be installed. 
- ``pex`` can compress python packages into a zip file that can be executed by any python interpreter.

Dependancies for paradrop are packaged with the final snap as a pex file created by freezing a virtualenv. These are the steps needed to do this:

1. ``venv.pex`` is packaged with paradrop source code. This is a pex that contains only the virtualenv package. This file bootstraps virtualenv so it does not need to be installed on the local system. 
2. A new virtual environment is created under ``/buildenv/env`` by calling ``venv.pex ./buildenv/env``
3. The environment is activated with ``source ./buildenv/env/bin/activate``. Any python package installations will now be placed here. 
4. Paradrop is installed with ``pip install -e .``. This installs paradrop in the virtual as well as all dependancies. Dependancies are listed in ``src/setup.py``. You must add depedencies here in order to include new python packages with paradrop. 
5. Dependancies are saved into ``bin/pddepedencies.pex`` with the command ``pex -r docs/requirements.txt -o bin/pddepedencies.pex``. Note: requirements are written out to the file in step 4. This is done so that the ``paradrop`` dependancy is not included in the pex, since pex won't know how to look for it! The command used to do this is ``pip freeze | grep -v 'pex' | grep -v 'paradrop' > docs/requirements.txt``.

At this point you can run paradrop by activating the virtualenv (step #3) and then simply calling ``paradrop``. Note that the bundled dependancies pex does not affect locally running paradrop instances-- its used in the next section.


Installing paradrop
--------------------
All programs installed on snappy are called ``snaps``. Snappy development tools are required to build snaps::

    sudo add-apt-repository ppa:snappy-dev/tools
    sudo apt-get update
    sudo apt-get install snappy-tools bzr

To build a snap::

    snappy build .

Push a snap to a running instance of snappy::

    snappy-remote --url=ssh://localhost:8022 install SNAPNAME


Creating chutes
--------------------

In progress.


## Contributing
All contributions must follow [PEP8](https://www.python.org/dev/peps/pep-0008/) and have relevant tests. Please document as needed. 

Compiling documentation
```
pip install sphinx sphinx-autobuild sphinx-rtd-build
cd docs
make html
```

sphinx-apidoc -f -o docs paradrop/paradrop/




