Base Images
===========

This directory contains the sources for light chute base images.  For each
language and architecture combination that we want to support, we will need to
build a base image.

Building
--------

These commands build base images for the x86_64 architecture.  We will also
add ARM images.

docker build -t paradrop/go-x86_64 go-x86_64
docker build -t paradrop/gradle-x86_64 gradle-x86_64
docker build -t paradrop/maven-x86_64 maven-x86_64
docker build -t paradrop/node-x86_64 node-x86_64
docker build -t paradrop/python2-x86_64 python2-x86_64
