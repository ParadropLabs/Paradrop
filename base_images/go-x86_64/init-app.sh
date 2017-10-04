#!/bin/sh

go get -d

# This will build a binary called "app" since we build out of /opt/paradrop/app.
go build
mv app /usr/local/bin
