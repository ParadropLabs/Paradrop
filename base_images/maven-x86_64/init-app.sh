#!/bin/bash

# Make maven output a little less verbose.
export MAVEN_OPTS=-Dorg.slf4j.simpleLogger.log.org.apache.maven.cli.transfer.Slf4jMavenTransferListener=warn

# If the app included a pom.xml file, then use maven to build it.
# --batch-mode disables the download progress bar.
if [ -f pom.xml ]; then
    mvn --batch-mode package
fi
