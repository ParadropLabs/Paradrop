#!/bin/sh
SCRIPT=`realpath -s $0`
SCRIPTPATH=`dirname $SCRIPT`

PYTHONPATH=$SCRIPTPATH python -m pdtools $@
