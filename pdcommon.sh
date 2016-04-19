#!/bin/bash

#############
# Static defines
###

#used to differentiate our output from other. Other output is still shown 
# in the case of errors
COLOR='\033[01;33m'

SNAPPY_VERSION="0.1.0"
DNSMASQ_SNAP="https://paradrop.io/storage/snaps/dnsmasq_2.74_all.snap"
HOSTAPD_SNAP="https://paradrop.io/storage/snaps/hostapd_2.4_all.snap"
PEX_CACHE="/var/lib/apps/paradrop/${SNAPPY_VERSION}/pex/install"
PARADROP_SNAP="https://paradrop.io/storage/snaps/v${SNAPPY_VERSION}/paradrop_${SNAPPY_VERSION}_all.snap"
PDINSTALL_SNAP="https://paradrop.io/storage/snaps/v${SNAPPY_VERSION}/pdinstall_${SNAPPY_VERSION}_all.snap"
PEX_CACHE="/var/lib/apps/paradrop/$SNAPPY_VERSION/pex/install"


#############
# build()
###
build() {
    echo "Cleaning build directories"

    rm -rf buildenv
    rm -rf paradrop/paradrop.egg-info
    rm -rf paradrop/build
    rm snaps/paradrop/bin/pd

    mkdir buildenv

    echo -e "${COLOR}Building paradrop" && tput sgr0

    if ! type "pex" > /dev/null; then
        echo 'Please install pex. Try:'
        echo "pip install pex"
        exit
    fi

    cd paradrop
    python setup.py bdist_egg -d ../buildenv
    cd ..
    if [ ! -f snaps/paradrop/bin/pipework ]; then
        wget https://raw.githubusercontent.com/jpetazzo/pipework/3bccb3adefe81b6acd97c50cfc6cda11420be109/pipework -O snaps/paradrop/bin/pipework
        chmod 755 snaps/paradrop/bin/pipework
    fi

    echo -e "${COLOR}Building paradrop-snap..." && tput sgr0

    #Unexpected, but it doesn't like trying to overrite the existing pex
    if [ -f snaps/paradrop/bin/pd ]; then
        rm snaps/paradrop/bin/pd
    fi

    pex --disable-cache paradrop -o snaps/paradrop/bin/pd -m paradrop:main -f buildenv/
    pex --disable-cache pdinstall -o snaps/pdinstall/bin/pdinstall -m pdinstall.main:main -f buildenv/
    rm -rf *.egg-info
}

#############
# Generate the docs
###
docs() {
    virtualenv buildenv/env
    source buildenv/env/bin/activate

    rm docs/requirements.txt
    pip install -e ./paradrop
    pip freeze | grep -v 'pex' | grep -v 'paradrop' > docs/requirements.txt
}

#############
# Cleans the build directories
###
clean() {
    echo "Cleaning build directories"

    rm -rf buildenv
    rm -rf paradrop/paradrop.egg-info
    rm snaps/paradrop/bin/pd
}

#############
#  Runs a local instance of paradrop
###
run() {
    echo -e "${COLOR}Starting Paradrop" && tput sgr0

    if [ ! -f snaps/paradrop/bin/pd ]; then
        echo "Dependency pex not found! Have you built the dependencies yet?"
        echo -e "\t$ $0 build"
        exit
    fi

    # Tell it to write to /tmp instead of the default location, so we know it
    # is writable for unprivileged users.
    export PDCONFD_WRITE_DIR="/tmp/pdconfd"
    export UCI_CONFIG_DIR="/tmp/config.d"
    export HOST_CONFIG_PATH="/tmp/hostconfig.yaml"

    snaps/paradrop/bin/pd
}

#############
#  Installs dnsmasq, docker, and hostapd on the target device
###
install_deps() {
    #assuming all snappy dev tools are installed if this one is (snappy-remote, for example)
    if ! type "snappy" > /dev/null; then
        echo 'Snappy development tools not installed. Try:'
        echo "$0 setup"
        exit
    fi

    # Remove an existing ssh key if it exists
    #   this is a required callback in pd[local|remote].sh
    removekey
    # Copy over the public key in the authorized keys file to prevent multiple password entries
    ssh-copy-id -p ${TARGET_PORT} ${TARGET}

    # Install docker
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

    echo -e "${COLOR}Getting official release snaps" && tput sgr0

    # Get the official snaps
    wget ${PARADROP_SNAP}
    wget ${PDINSTALL_SNAP}

    echo -e "${COLOR}Installing snap" && tput sgr0
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "paradrop_${SNAPPY_VERSION}_all.snap"
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "pdinstall_${SNAPPY_VERSION}_all.snap"
    rm *.snap

    exit
}

# If there is a failed install of paradrop, we need to clean up the files that are still around
# in order to attempt a second install
uninstall() {
    ssh -p 8022 ubuntu@localhost sudo snappy remove pdinstall
    ssh -p 8022 ubuntu@localhost sudo snappy remove paradrop
    ssh -p 8022 ubuntu@localhost sudo rm -rf /writable/system-data/var/lib/apps/paradrop \
        /writable/system-data/etc/dbus-1/system.d/paradrop_pd_* \
        /writable/system-data/etc/systemd/system/paradrop_pd_* \
        /writable/system-data/etc/systemd/system/multi-user.target.wants/paradrop_pd_* \
        /writable/system-data/var/lib/snappy/apparmor/policygroups/paradrop_client \
        /writable/system-data/var/lib/snappy/seccomp/profiles/paradrop_pd_* \
        /writable/system-data/var/lib/snappy/seccomp/policygroups/paradrop_client \
        /writable/system-data/var/lib/apparmor/snappy/profiles/paradrop_pd_* \
        /writable/system-data/var/lib/apps/paradrop \
        /writable/system-data/apps/paradrop \
        /etc/systemd/system/paradrop_pd_* \
        /etc/systemd/system/multi-user.target.wants/paradrop_pd_* \
        /etc/dbus-1/system.d/paradrop_pd_* \
        /apps/paradrop \
        /var/lib/snappy/apparmor/policygroups/paradrop_client \
        /var/lib/snappy/seccomp/profiles/paradrop_pd_* \
        /var/lib/snappy/seccomp/policygroups/paradrop_client \
        /var/lib/apparmor/snappy/profiles/paradrop_pd_* \
        /var/lib/apps/paradrop
}

update-tools() {
    cd pdtools

    python setup.py sdist bdist_wheel
    twine upload dist/* 

    rm -rf build/ dist/ *.egg-info

    sudo pip install pdtools -U
}

