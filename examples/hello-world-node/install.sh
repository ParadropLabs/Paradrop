#!/bin/sh

mkdir -p deployment/chute
cp -r development/node_modules deployment/chute
cp development/package.json deployment/chute
cp development/server.js deployment/chute
