# Paradrop

[![Join the chat at https://gitter.im/damouse/Paradrop](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/damouse/Paradrop?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Documentation Status](https://readthedocs.org/projects/paradrop/badge/?version=latest)](https://readthedocs.org/projects/paradrop/?badge=latest)


Virtualized wireless routers. 

Work in progress. For now, assume everything here is subject to change. 

## Installation
Getting started with paradrop.

### Snappy
[Snappy](https://developer.ubuntu.com/en/snappy/) is an Ubuntu release focusing on low-overhead for a large set of platforms. These instructions are for getting a Snappy instance up and running using 'kvm'. 

Download and unzip a snappy image 
```
wget http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz
unxz ubuntu-15.04-snappy-amd64-generic.img.xz
```

Launch the snappy image using kvm
```
kvm -m 512 -redir :8090::80 -redir :8022::22 ubuntu-15.04-snappy-amd64-generic.img
```

Connect to local instance using ssh
```
ssh -p 8022 ubuntu@localhost
```

### Paradrop
Paradrop is packaged as a python package. This means you can install it on a local system without needing to interact with snappy. Be warned-- the package on its own assumes that docker and Open vSwitch are installed, and may fail if these components are not already installed!

(in progress)


Build a Snap and push it to a running snappy instance. Make sure you're in the directory you're trying to build before attempting these steps. This example loads one the sample snappy apps. 
```
snappy build .
snappy-remote --url=ssh://localhost:8022 install ./hello-world_1.0.17_all.snap
```

Snaps with binaries must have those binaries explicitly called. Those with services are automatically started. This example again uses the sample 'hello-world' shipped with the snappy examples repository.
```
hello-world.echo
```


### Virtualenv
(Note: not using virtualenv for pex configuration later, but it makes things easier.)
virtualenv is a tool that allows developers to manage environments, dependancies and more for python programs. In this case its used both as a management tool and a packageing tool (along with pex.)

We may choose to go with this as part of the build process since it doesn't require building the python package, but perhaps not. 

To load the current virtualenv, use 
    source [envdir]/bin/activate

To deactivate, use
    deactivate

To install something like twisted be sure to have python developer tools already installed:
    sudo apt-get install python-dev

## Contributing
All contributions must follow [PEP8](https://www.python.org/dev/peps/pep-0008/) and have relevant tests. Please document as needed. 

## Miscellanious Help

