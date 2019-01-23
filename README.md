# Paradrop

[![Documentation Status](https://readthedocs.org/projects/paradrop/badge/?version=latest)](https://readthedocs.org/projects/paradrop/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/ParadropLabs/Paradrop/badge.svg?branch=master)](https://coveralls.io/github/ParadropLabs/Paradrop?branch=master)
[![Build Status](https://travis-ci.org/ParadropLabs/Paradrop.svg?branch=master)](https://travis-ci.org/ParadropLabs/Paradrop)
[![Snap Status](https://build.snapcraft.io/badge/ParadropLabs/Paradrop.svg)](https://build.snapcraft.io/user/ParadropLabs/Paradrop)
![Docker Image](https://img.shields.io/docker/pulls/paradrop/daemon.svg)(https://hub.docker.com/r/paradrop/daemon)

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-white.svg)](https://snapcraft.io/paradrop-agent)

## What is Paradrop?

Paradrop is a software platform that brings the *cloud into the home* by enabling apps to exist on Wi-Fi routers. The Wi-Fi router is the last always-on, always-connected, ubiquitous device in the home today. At Paradrop Labs, we believe that some (if not most) cloud or smart-hub services should actually exist on Wi-Fi routers.

Read our [paper](http://pages.cs.wisc.edu/~suman/courses/707/papers/paradrop-sec2016.pdf) or visit our [website](https://www.paradrop.org) to learn more!


## What can I do with Paradrop?

Since Wi-Fi routers are the central nervous system for all Internet based services in the home, the possibilities are quite endless. We have implemented many example applications, you can see the source code [here](https://github.com/ParadropLabs/Example-Apps). We encourage you to test out Paradrop by cloning our repo and checking out our [getting started](http://paradrop.readthedocs.org/en/latest/#getting-started) page.


## Get Started

Paradrop uses Docker containers to run edge computing services, but
Paradrop itself can also run as a Docker container. This is a good
option if you want to try out Paradrop's core functionality without
using special hardware or changing your operating system.

### Docker Container in Safe Mode

Run the following command if you only want to test the core edge
computing functionality.  This will allow you to install and remove
chutes, experiment with the edge API and connect the node to the cloud
controller. Since this command creates a container separated from the
host network, Paradrop will not be able to manage the network interfaces,
wireless networks, and firewall settings of the host operating system.

```bash
docker run --privileged --name paradrop --publish 8080:80 -v /var/run/docker.sock:/var/run/docker.sock paradrop/daemon
```

After the Paradrop daemon is running, you can access the admin panel with
a web browser by going to http://localhost:8080. If prompted, enter the
user name *paradrop* and no password. You can also use `pdtools node`
commands such as the `install-chute` command. The following example
assumes you are running it from a directory containing the source code
for a chute, which means there should be a valid *paradrop.yaml* file
in the directory.

```bash
pdtools node --target localhost:8080 install-chute
```

### Docker Container with Host Network Access

Run the following command if you want to test all of Paradrop's functions.
Giving the Paradrop container access to the host network stack will enable
it to manage network interfaces, wireless networks, and firewall settings.
By default, Paradrop will try to create a wireless access point using one
of the machine's WiFi interfaces. **Warning:** because Paradrop will make
potentially disruptive system configuration changes, we do not recommend
running Paradrop using the following command on a workstation that you
use for other purposes. Consider running it in a virtual machine instead.

```bash
docker run --privileged --name paradrop --net=host -v /var/run/docker.sock:/var/run/docker.sock paradrop/daemon
```

You can access the Paradrop node in the same way as described in the
Safe Mode section above. However, the node is listening directly on
the host port 80. That means you can access http://localhost or use
`pdtools node --target localhost`.

## Preparing a new release

1. Merge changes into the master branch.
2. Run `./pdbuild.sh release <version>` to update version number and tag the release.
3. Run `./pdbuild.sh build` to build a new snap.
4. Run `./pdbuild.sh image` to build a new disk image.

