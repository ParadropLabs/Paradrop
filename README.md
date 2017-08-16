# Paradrop

[![Documentation Status](https://readthedocs.org/projects/paradrop/badge/?version=latest)](https://readthedocs.org/projects/paradrop/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/ParadropLabs/Paradrop/badge.svg?branch=master)](https://coveralls.io/r/ParadropLabs/Paradrop?branch=master)
[![Build Status](https://travis-ci.org/ParadropLabs/Paradrop.svg?branch=dev)](https://travis-ci.org/ParadropLabs/Paradrop)

## What is Paradrop?

Paradrop is a software platform that brings the *cloud into the home* by enabling apps to exist on Wi-Fi routers. The Wi-Fi router is the last always-on, always-connected, ubiquitous device in the home today. At Paradrop Labs, we believe that some (if not most) cloud or smart-hub services should actually exist on Wi-Fi routers.

Visit our [website](https://www.paradrop.org) to learn more!


## What can I do with Paradrop?

Since Wi-Fi routers are the central nervous system for all Internet based services in the home, the possibilities are quite endless. We have implemented many example applications, you can see the source code [here](https://github.com/ParadropLabs/Example-Apps). We encourage you to test out Paradrop by cloning our repo and checking out our [getting started](http://paradrop.readthedocs.org/en/latest/#getting-started) page.


## Preparing a new release

1. Merge changes into the master branch.
2. Run `./pdbuild.sh release <version>` to update version number and tag the release.
3. Run `./pdbuild.sh build` to build a new snap.
4. Run `./pdbuild.sh image` to build a new disk image.

