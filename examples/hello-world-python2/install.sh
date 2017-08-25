#!/bin/sh

mkdir -p deployment/chute
cp development/setup.py deployment/chute/
cp -r development/helloworld/*.py deployment/chute/helloworld/
