#!/bin/bash

# If the app included a pom.xml file, then use maven to build it.
# --batch-mode disables the download progress bar.
if [ -f pom.xml ]; then
    mvn --batch-mode dependency:resolve
fi
