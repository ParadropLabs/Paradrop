# Paradrop

[![Documentation Status](https://readthedocs.org/projects/paradrop/badge/?version=latest)](https://readthedocs.org/projects/paradrop/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/ParadropLabs/Paradrop/badge.svg?branch=master)](https://coveralls.io/github/ParadropLabs/Paradrop?branch=master)
[![Build Status](https://travis-ci.org/ParadropLabs/Paradrop.svg?branch=master)](https://travis-ci.org/ParadropLabs/Paradrop)
[![Snap Status](https://build.snapcraft.io/badge/ParadropLabs/Paradrop.svg)](https://build.snapcraft.io/user/ParadropLabs/Paradrop)
[![Docker Image](https://img.shields.io/docker/pulls/paradrop/daemon.svg)](https://hub.docker.com/r/paradrop/daemon)

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

## Applications

Paradrop is just a platform for running edge computing applications,
which we call *chutes*.  Once you have a Paradrop node running, you may
want to check out one or more of the following example chutes that can
run on Paradrop.

* [captive-portal](https://github.com/ParadropLabs/captive-portal)
  This chute creates a WiFi network that uses iptables rules to
  redirect users to a landing when they first connect to the network.
  It works nicely with CNA implementations on most popular devices.
* [Cells](https://github.com/ParadropLabs/Cells)
  A multiplayer browser-based action game where players take control
  of a cell. The goal is to gain as much mass as possible by eating
  food and smaller cells and avoid being eaten. The code was developed
  by another team and adapted to run on Paradrop.
* [Drop64](https://github.com/ParadropLabs/Drop64)
  Run a Nintendo 64 emulator in a browser window. This chute was
  created by using emscripten to compile mupen64plus to JavaScript.
* [go-hello-world](https://github.com/ParadropLabs/go-hello-world)
  Example chute that implements a web server in Go.
* [gradle-hello-world](https://github.com/ParadropLabs/gradle-hello-world)
  Example chute that implements a web server using Java and Gradle.
* [node-hello-world](https://github.com/ParadropLabs/node-hello-world)
  Example chute that implements a web server using Node.js.
* [ParentalControlStarterChute](https://github.com/ParadropLabs/ParentalControlStarterChute)
  This chute creates a WiFi network that implements content filtering at
  the HTTP and DNS levels. This code has been used in tutorials, so it
  is intended to be a starting point rather than a complete application.
* [python-socket-example](https://github.com/ParadropLabs/python-socket-example)
  Example chute that implements a basic TCP server in Python along with
  example client code.
* [Security-Camera](https://github.com/ParadropLabs/Security-Camera)
  This chute works with wireless cameras to implement basic motion
  detection. The code has been used in tutorials, so it is more of a
  starting point than a complete application.
* [StickyBoard](https://github.com/ParadropLabs/StickyBoard)
  This project demonstrates using edge computing for localized content.
  Users who connect to the Paradrop node are able to post pictures
  on the "sticky board" that are only viewable by other people on the
  same network.
* [traffic-camera](https://github.com/ParadropLabs/traffic-camera)
  This chute demonstrates a computer vision task implemented at the
  edge. It uses an OpenCV cascade classifier to detect and count vehicles
  in video from a traffic camera.
* [WiFiSense](https://github.com/ParadropLabs/WiFiSense)
  This chute uses WiFi monitor mode to detect nearby devices and send
  periodic reports to a configurable server. Running this on multiple
  Paradrop nodes could be used to implement interesting behavior
  analytics.
* [wiki](https://github.com/ParadropLabs/wiki)
  This project implements a simple wiki page. The code is from an open
  source project that was adapted to run on Paradrop.

## Preparing a new release

1. Merge changes into the master branch.
2. Run `./pdbuild.sh release <version>` to update version number and tag the release.
3. Run `./pdbuild.sh build` to build a new snap.
4. Run `./pdbuild.sh image` to build a new disk image.
