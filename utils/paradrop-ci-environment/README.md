CI Environment Image
====================

This directory contains the source for the paradrop-ci-environment Docker
image, which is used as an environment for running unit tests and build
tasks on the Paradrop code.

Building
--------

From this directory, run:

    docker build -t paradrop/paradrop-ci-environment .

Push it to Docker hub. You need to have access to the paradrop namespace first.

    docker push paradrop/paradrop-ci-environment
