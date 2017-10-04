#!/bin/sh

# If the app included a build.gradle file, then use gradle to build it.
if [ -f build.gradle ]; then
    gradle build
fi
