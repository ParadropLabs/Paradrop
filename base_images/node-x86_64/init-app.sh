#!/bin/bash

# Reduce logging output from npm to just warnings and errors.
export npm_config_loglevel=warn

# The app may have shipped with binary libraries built for a different
# architecture (node_modules directory checked into source control).
# `npm rebuild` should fix them.
npm rebuild

# If the app included a package.json file, then use npm to install dependencies.
if [ -f package.json ]; then
    npm install
fi
