#!/bin/bash

source $SNAP/bin/env.sh
export PDSERVER_URL=$PDSERVER_URL_PRODUCTION

$SNAP/bin/paradrop
