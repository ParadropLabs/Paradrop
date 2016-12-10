#!/bin/bash

#used to differentiate our output from other. Other output is still shown
# in the case of errors
COLOR='\033[01;33m'

# Perhaps overkill, but preps the local environment for snappy testing

printhelp() {
    echo -e "${COLOR}Paradrop build tools." && tput sgr0
    echo -e "${COLOR}Please use Ubuntu 16.04+ as the development machine!\n" && tput sgr0
    echo -e "This tool installs all needed dependencies in a local virtual environment and set up Snappy development\n"

    echo "Usage:"
    echo -e "  setup\t\t prepares environment for development"
    echo -e "  run\t\t run paradrop locally"
    echo -e "  build\t\t build snaps"
    echo -e "  test\t\t run unit tests"
    echo -e "  docs\t\t rebuilds sphinx docs for readthedocs"
    exit
}

setup() {
    echo -e "${COLOR}Setting up virtualenv" && tput sgr0
    if [ ! -f /usr/local/bin/virtualenv ]; then
        sudo apt-get install python-setuptools python-dev build-essential libcurl4-gnutls-dev libffi-dev
        sudo easy_install pip
        sudo pip install --upgrade virtualenv
    fi

    if ! type "snapcraft" > /dev/null; then
        echo -e "${COLOR} Installing snappy tools" && tput sgr0
        sudo apt-get update
        sudo apt-get install snapcraft
    fi

    echo -e "${COLOR}Snappy development tools installed" && tput sgr0

    virtualenv buildenv/env
    pip install -r requirements.txt
}

build() {
    (cd paradrop; snapcraft)     
}

test() {
    source buildenv/env/bin/activate
    nosetests
}

docs() {
    source buildenv/env/bin/activate
    rm docs/requirements.txt
    pip install -e ./paradrop/src
    pip freeze | grep -v 'paradrop' > docs/requirements.txt
}

clean() {
    echo "Cleaning build directories"
    (cd paradrop; snapcraft clean)
}

run() {
    echo -e "${COLOR}Starting Paradrop" && tput sgr0
    echo "TODO..."
}

#Show help if no args passed
if [ $# -lt 1 ]
then
    printhelp
fi

###
# Call Operations
###
case "$1" in
    "help") printhelp;;
    "--help") printhelp;;
    "setup") setup;;
    "test") test;;
    "build") build;;
    "clean") clean;;
    "run") run;;
    "docs") docs;;
    *) echo "Unknown input $1"
   ;;
esac
