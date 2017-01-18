#!/bin/bash

# Fix permissions issues because Docker adds everything as root.
chown --recursive $USER .

# If the app included a requirements.txt file, then use pip to install dependencies.
if [ -f requirements.txt ]; then
    pip install --requirement requirements.txt --user
fi
