#!/bin/bash 

# Include the remote address of the device
source pdremote.conf

#used to differentiate our output from other. Other output is still shown 
# in the case of errors
COLOR='\033[01;33m' 

SNAPPY_VERSION="0.1.0"
DNSMASQ_SNAP="https://paradrop.io/storage/snaps/dnsmasq_2.74_all.snap"
HOSTAPD_SNAP="https://paradrop.io/storage/snaps/hostapd_2.4_all.snap"
PEX_CACHE="/var/lib/apps/paradrop/$SNAPPY_VERSION/pex/install"
PARADROP_SNAP="https://paradrop.io/storage/snaps/v$SNAPPY_VERSION/paradrop_$SNAPPY_VERSION_all.snap"
PDINSTALL_SNAP="https://paradrop.io/storage/snaps/v$SNAPPY_VERSION/pdinstall_$SNAPPY_VERSION_all.snap"

#Show help if no args passed
if [ $# -lt 1 ]
then
    echo -e "${COLOR}Paradrop build tools." && tput sgr0
    echo -e "This tool installs all needed dependencies in a local virtual environment and can set up Snappy development\n"

    echo -e "To get paradrop on a snappy instance as quickly as possible, run build and install\n"

    echo "Usage:"
    echo -e "  build\t\t build and package dependencies, install paradrop locally"
    # echo -e "  clean\n\t remove virtual environment, clean packages"
    echo -e "  install \t get official snap and install on the remote machine."
    echo -e "  install_dev \t get official snap and install on the remote machine."
    echo -e "  setup\t\t prepares environment for snappy testing"
    echo -e "  reboot\t\t reboots the hardware properly"
    echo -e "  connect\t connects to the snappy machine"
    echo -e "  check\t\t checks the state of the Paradrop instance tools in the device"
    echo -e "  logs\t\t print out the logs from in the machine directly to screen (only use to debug issues)"

    echo -e "\nDevelopment operations"
    echo -e "  docs\t\t rebuilds sphinx docs for readthedocs"
    echo -e "  update-tools\t uploads build tools to pypi. Requires authentication."
    exit
fi

###
# Operations
###

#  commented lines are from the older virtualenv way of packaging the app. This seems cleaner
build() {
    echo "Cleaning build directories"

    rm -rf buildenv
    rm -rf paradrop/paradrop.egg-info
    rm -rf paradrop/build
    rm snaps/paradrop/bin/pd

    mkdir buildenv

    echo -e "${COLOR}Loading and building python dependencies"
    # echo -e "${COLOR}Bootstrapping environment" && tput sgr0

    # ./venv.pex buildenv/env
    # source buildenv/env/bin/activate

    echo -e "${COLOR}Installing paradrop" && tput sgr0

    if ! type "pex" > /dev/null; then
        echo 'Please install pex. Try:'
        echo "pip install pex"
        exit
    fi

    # pip install pex
    # pip install -e ./paradrop

    #also-- we can get away without saving the requirements just fine, but readthedocs needs them
    # pip freeze | grep -v 'pex' | grep -v 'paradrop' > docs/requirements.txt
    # pex -r docs/requirements.txt -o snap/bin/pd.pex -m paradrop.main:main -f buildenv/dist

    # pip and bdist doesn't play well together. Turn off the virtualenv.
    # deactivate 

    #the above is somewhat redundant now, but meh
    cd paradrop
    python setup.py bdist_egg -d ../buildenv
    cd ..
    if [ ! -f snaps/paradrop/bin/pipework ]; then
        wget https://raw.githubusercontent.com/jpetazzo/pipework/3bccb3adefe81b6acd97c50cfc6cda11420be109/pipework -O snaps/paradrop/bin/pipework
        chmod 755 snaps/paradrop/bin/pipework
    fi

    echo -e "${COLOR}Building paradrop-snappy..." && tput sgr0
    
    #Unexpected, but it doesn't like trying to overrite the existing pex
    if [ -f snaps/paradrop/bin/pd ]; then
        rm snaps/paradrop/bin/pd
    fi

    pex --disable-cache paradrop -o snaps/paradrop/bin/pd -m paradrop:main -f buildenv/
    pex --disable-cache pdinstall -o snaps/pdinstall/bin/pdinstall -m pdinstall.main:main -f buildenv/
    rm -rf *.egg-info
}

# Generates docs 
docs() {
    virtualenv buildenv/env
    source buildenv/env/bin/activate

    rm docs/requirements.txt
    pip install -e ./paradrop
    pip freeze | grep -v 'pex' | grep -v 'paradrop' > docs/requirements.txt
}

clean() {
    echo "Cleaning build directories"

    rm -rf buildenv
    rm -rf paradrop/paradrop.egg-info
    rm snaps/paradrop/bin/pd
}

install_deps() {
    #assuming all snappy dev tools are installed if this one is (snappy-remote, for example)
    if ! type "snappy" > /dev/null; then
        echo 'Snappy development tools not installed. Try:'
        echo "$0 setup"
        exit
    fi

    # copy the ssh key over to prevent entering the password many times
    ssh-copy-id -p ${TARGET_PORT} ${TARGET}

    ssh -p ${TARGET_PORT} ${TARGET} sudo snappy install docker

    wget --quiet $DNSMASQ_SNAP
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install dnsmasq*.snap
    rm dnsmasq*.snap

    wget --quiet $HOSTAPD_SNAP
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install hostapd*.snap
    rm hostapd*.snap
}

install_dev() {
    if [ ! -f snaps/paradrop/bin/pd ]; then
        echo "Dependency pex not found! Have you built the dependencies yet?"
        echo -e "\t$ $0 build"
        exit
    fi

    #assuming all snappy dev tools are installed if this one is (snappy-remote, for example)
    if ! type "snappy" > /dev/null; then
        echo 'Snappy development tools not installed. Try:'
        echo "$0 setup"
        exit
    fi

    echo -e "${COLOR}Purging pex cache on target" && tput sgr0
    ssh -p ${TARGET_PORT} ${TARGET} sudo rm -rf "$PEX_CACHE"

    echo -e "${COLOR}Building snap" && tput sgr0
    
    #build the snap using snappy dev tools and extract the name of the snap
    snappy build snaps/paradrop
    snappy build snaps/pdinstall

    echo -e "${COLOR}Installing snap" && tput sgr0
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "paradrop_${SNAPPY_VERSION}_all.snap"
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "pdinstall_${SNAPPY_VERSION}_all.snap"
    rm *.snap
    
    exit
}

install() {
    #assuming all snappy dev tools are installed if this one is (snappy-remote, for example)
    if ! type "snappy" > /dev/null; then
        echo 'Snappy development tools not installed. Try:'
        echo "$0 setup"
        exit
    fi

    echo -e "${COLOR}Purging pex cache on target" && tput sgr0
    ssh -p ${TARGET_PORT} ${TARGET} sudo rm -rf "$PEX_CACHE"

    echo -e "${COLOR}Building snap" && tput sgr0
    
    # Get the official snaps
    wget ${PARADROP_SNAP}
    wget ${PDINSTALL_SNAP}

    echo -e "${COLOR}Installing snap" && tput sgr0
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "paradrop_${SNAPPY_VERSION}_all.snap"
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "pdinstall_${SNAPPY_VERSION}_all.snap"
    rm *.snap
    
    exit
}

# Perhaps overkill, but preps the local environment for snappy testing
setup() {
    if ! type "snappy" > /dev/null; then
        echo -e "${COLOR} Installing snappy tools" && tput sgr0
        sudo add-apt-repository ppa:snappy-dev/tools
        sudo apt-get update
        sudo apt-get install snappy-tools bzr
    fi

    echo -e "${COLOR}Snappy development tools installed" && tput sgr0
}

reboot() {
    echo -e "${COLOR} Rebooting the hardware" && tput sgr0
    ssh -p ${TARGET_PORT} ${TARGET} sudo reboot
}

connect() {
    echo -e "${COLOR} Connecting to the hardware user: ubuntu password: ubuntu" && tput sgr0
    ssh -p ${TARGET_PORT} ${TARGET}
}

check() {
    ssh -p ${TARGET_PORT} ${TARGET} systemctl status paradrop_pd_${SNAPPY_VERSION}.service
}

logs() {
    ssh -p ${TARGET_PORT} ${TARGET} sudo /apps/paradrop/current/bin/dump_log.py
}

update-tools() {
    cd pdtools

    python setup.py sdist bdist_wheel
    twine upload dist/* 

    rm -rf build/ dist/ *.egg-info

    sudo pip install pdtools -U
}

###
# Call Operations
###

case "$1" in
    "build") build;;
    # "clean") clean;;
    "install_deps") install_deps;;
    "install") install;;
    "install_dev") install_dev;;
    "setup") setup;;
    "connect") connect;;
    "reboot") reboot;;
    "check") check;;
    "docs") docs;;
    "logs") logs;;
    "update-tools") update-tools;;
    *) echo "Unknown input $1"
   ;;
esac
