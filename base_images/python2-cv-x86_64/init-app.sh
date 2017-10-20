#!/bin/bash

# If the app included a requirements.txt file, then use pip to install dependencies.
if [ -f requirements.txt ]; then
    pip install --requirement requirements.txt
fi
