Base Images
===========

This directory contains the sources for light chute base images.  For each
language and architecture combination that we want to support, we will need to
build a base image.

Building
--------

This command builds the node.js image.  More will be added later, including ARM
images.

docker build -t paradrop/node-x86_64 node-x86_64
