#!/bin/bash

#############
# Static defines
###
source pdbuild.conf

#used to differentiate our output from other. Other output is still shown 
# in the case of errors
COLOR='\033[01;33m'

DEV_SNAPPY_VERSION="0.2.0"
RELEASE_SNAPPY_VERSION="0.1.0"
DNSMASQ_SNAP="https://paradrop.io/storage/snaps/dnsmasq_2.74_all.snap"
HOSTAPD_SNAP="https://paradrop.io/storage/snaps/hostapd_2.4_all.snap"
PEX_CACHE="/var/lib/apps/paradrop/${DEV_SNAPPY_VERSION}/pex/install"
PARADROP_SNAP="https://paradrop.io/storage/snaps/v${RELEASE_SNAPPY_VERSION}/paradrop_${RELEASE_SNAPPY_VERSION}_all.snap"
PDINSTALL_SNAP="https://paradrop.io/storage/snaps/v${RELEASE_SNAPPY_VERSION}/pdinstall_${RELEASE_SNAPPY_VERSION}_all.snap"
PEX_CACHE="/var/lib/apps/paradrop/$DEV_SNAPPY_VERSION/pex/install"
LOCALWEB_LOCATION="paradrop/localweb/."

if [ "$INSTANCE" = "remote" ]; then
    ENVIRONMENT="remote"
elif [ "$INSTANCE" = "local" ]; then
    ENVIRONMENT="virtual"
    TARGET="ubuntu@localhost"
    TARGET_PORT="8022"
fi

#############
# Utils
###
killvm() {
    if [ -f pid.txt ]; then
        echo -e "${COLOR}Killing snappy virtual machine" && tput sgr0
        KVM="$(cat pid.txt)"
        kill "${KVM}"
        rm pid.txt
    else
        echo -e "${COLOR}Snappy virtual machine is not running" && tput sgr0
    fi
}

down() {
    killvm
}

# Removes the ssh key in known_hosts
removekey() {
    echo -e 'Removing old ssh key pair'
    if [ $ENVIRONMENT = "virtual" ]; then
        # Remove the localhost key if they started a different image
        ssh-keygen -f "~/.ssh/known_hosts" -R [localhost]:8022
    else
        ssh-keygen -f "~/.ssh/known_hosts" -R ${TARGET}
    fi
}

# Perhaps overkill, but preps the local environment for snappy testing
setup() {
    if [ $ENVIRONMENT = "virtual" ]; then
        if ! type "kvm" > /dev/null; then
            echo -e '${COLOR}Installing kvm' && tput sgr0
            sudo apt-get install qemu-kvm -y
        fi

        #check for image only download if it does not already exist
        if [ ! -f snappy-vm.img ]; then
            echo -e "${COLOR}Downloading Snappy image." && tput sgr0

            if ! [ -d "./buildenv" ]; then
                mkdir buildenv
            fi

            wget http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz 
            unxz ubuntu-15.04-snappy-amd64-generic.img.xz
            mv ubuntu-15.04-snappy-amd64-generic.img snappy-vm.img
            rm -rf releases.ubuntu.com
        fi
    fi
    if ! type "snappy" > /dev/null; then
        echo -e "${COLOR} Installing snappy tools" && tput sgr0
        sudo add-apt-repository ppa:snappy-dev/tools
        sudo apt-get update
        sudo apt-get install snappy-tools bzr
    fi

    echo -e "${COLOR}Snappy development tools installed" && tput sgr0
}

up() {
    if [ $ENVIRONMENT = "virtual" ]; then
        if [ -f pid.txt ]; then
            echo "Snappy virtual machine is already running. If you believe this to be an error, try:"
            echo -e "$0 down"
            exit
        fi

        if [ ! -f snappy-vm.img ]; then
            echo "Snappy image not found. Try:"
            echo -e "\t$0 setup"
            exit
        fi

        # Check for WiFi arg
        if [ ! -z "$1" ]; then
            WIFI=(`echo "$1" | tr "-" " "`)
            WIFI_BUS="${WIFI[1]}"
            WIFI_ADDR="${WIFI[2]}"
            echo "Enabling wifi with $WIFI_BUS:$WIFI_ADDR"
            WIFI_CMD="-usb -device usb-host,hostbus=$WIFI_BUS,hostaddr=$WIFI_ADDR"
        else
            WIFI_CMD=""
        fi

        echo "Starting snappy instance on local ssh port 8022."
        echo "Please wait for the virtual machine to load."
        echo "Default username:password is ubuntu:ubuntu."

        if [ ! -f /dev/kvm ]; then
           #qemu-system-x86_64 -nographic -m 512 -netdev user,id=net0,hostfwd=tcp::8090-:80,hostfwd=tcp::8022-:22,hostfwd=tcp::9999-:14321,hostfwd=tcp::9000-:9000 \
           qemu-system-x86_64 -nographic -vga none -m 512 -netdev user,id=net0,hostfwd=tcp::8090-:80,hostfwd=tcp::8022-:22,hostfwd=tcp::9999-:14321,hostfwd=tcp::9000-:9000 \
                -netdev user,id=net1 -device e1000,netdev=net0 -device e1000,netdev=net1 $WIFI_CMD snappy-vm.img &
        else
            if [ `pidof X` ]; then
                kvm -m 512 -netdev user,id=net0,hostfwd=tcp::8090-:80,hostfwd=tcp::8022-:22,hostfwd=tcp::9999-:14321,hostfwd=tcp::9000-:9000 \
                    -netdev user,id=net1 -device e1000,netdev=net0 -device e1000,netdev=net1 $WIFI_CMD snappy-vm.img &
            else
                kvm -m 512 -netdev user,id=net0,hostfwd=tcp::8090-:80,hostfwd=tcp::8022-:22,hostfwd=tcp::9999-:14321,hostfwd=tcp::9000-:9000 \
                    -netdev user,id=net1 -device e1000,netdev=net0 -device e1000,netdev=net1 $WIFI_CMD -nographic snappy-vm.img &
            fi
        fi

        # mickey has trouble with the kvm forwarding numbers. Might be something already on the port
        # kvm -m 512 -netdev user,id=net0,hostfwd=tcp::8090-:80,hostfwd=tcp::8022-:22,hostfwd=tcp::9999-:14321,hostfwd=tcp::9001-:9000 \
        #         -netdev user,id=net1 -device e1000,netdev=net0 -device e1000,netdev=net1 $WIFI_CMD snappy-vm.img &

        echo $! > pid.txt
    else
        echo "Instance is set to remove, exiting..."
    fi
}


#############
# Help
###

printhelp() {
    echo -e "${COLOR}Paradrop build tools." && tput sgr0
    echo -e "This tool installs all needed dependencies in a local virtual environment and can set up Snappy development\n"

    echo -e "To get paradrop on a snappy instance as quickly as possible, run build and install\n"

    echo "Usage:"
    echo -e "  build\t\t build and package dependencies, install paradrop locally"
    # echo -e "  clean\n\t remove virtual environment, clean packages"
    echo -e "  run\t\t run paradrop locally"
    echo -e "  install \t compile snap and install on snappy ${ENVIRONMENT} machine."
    echo -e "  install_dev \t build the paradrop snaps and install on the ${ENVIRONMENT} machine."
    echo -e "  uninstall \t removes paradrop from the ${ENVIRONMENT} machine"
    echo -e "  setup\t\t prepares environment for local snappy testing"
    echo -e "  up\t\t starts a local snappy virtual machine, add wifi interface with 'up wifi-BUS-ADDR'"
    echo -e "  down\t\t closes a local snappy virtual machine"
    echo -e "  reboot\t\t reboots the ${ENVIRONMENT} machine properly"
    echo -e "  connect\t ssh connect to snappy ${ENVIRONMENT} machine"
    echo -e "  check\t\t checks the state of the ${ENVIRONMENT} machine and Paradrop instance tools in the ${ENVIRONMENT} machine"
    echo -e "  logs\t\t print out the logs from in the ${ENVIRONMENT} machine directly to screen (only use to debug issues)"

    echo -e "\nDevelopment operations"
    echo -e "  docs\t\t rebuilds sphinx docs for readthedocs"
    echo -e "  update-tools\t uploads build tools to pypi. Requires authentication."
    exit
}

#############
# build()
###
build() {
    echo "Cleaning build directories"

    rm -rf buildenv
    rm -rf paradrop/paradrop.egg-info
    rm -rf paradrop/build
    rm -f snappy_v1/paradrop/bin/pd

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

    cd pdtools
    python setup.py bdist_egg -d ../buildenv
    cd ..

    if [ ! -f snappy_v1/paradrop/bin/pipework ]; then
        wget https://raw.githubusercontent.com/jpetazzo/pipework/3bccb3adefe81b6acd97c50cfc6cda11420be109/pipework -O snappy_v1/paradrop/bin/pipework
        chmod 755 snappy_v1/paradrop/bin/pipework
    fi

    echo -e "${COLOR}Building paradrop-snap..." && tput sgr0

    #Unexpected, but it doesn't like trying to overrite the existing pex
    if [ -f snappy_v1/paradrop/bin/pd ]; then
        rm snappy_v1/paradrop/bin/pd
    fi

    pex --disable-cache paradrop -o snappy_v1/paradrop/bin/pd -m paradrop:main -f buildenv/
    pex --disable-cache pdinstall -o snappy_v1/pdinstall/bin/pdinstall -m pdinstall.main:main -f buildenv/
    rm -rf *.egg-info

    #build the snap using snappy dev tools and extract the name of the snap
    snappy build snappy_v1/paradrop -o snappy_v1
    snappy build snappy_v1/pdinstall -o snappy_v1
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
    rm snappy_v1/paradrop/bin/pd
}

#############
#  Runs a local instance of paradrop
###
run() {
    echo -e "${COLOR}Starting Paradrop" && tput sgr0

    if [ ! -f snappy_v1/paradrop/bin/pd ]; then
        echo "Dependency pex not found! Have you built the dependencies yet?"
        echo -e "\t$ $0 build"
        exit
    fi

    source snappy_v1/paradrop/bin/env.sh
    snappy_v1/paradrop/bin/pd -l
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
    if [ ! -f snappy_v1/paradrop/bin/pd ]; then
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

    echo -e "${COLOR}Installing snap" && tput sgr0
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "snappy_v1/paradrop_${DEV_SNAPPY_VERSION}_all.snap"
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "snappy_v1/pdinstall_${DEV_SNAPPY_VERSION}_all.snap"

    exit
}

install() {
    if [ ! -f snappy_v1/paradrop/bin/pd ]; then
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
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "paradrop_${RELEASE_SNAPPY_VERSION}_all.snap"
    snappy-remote --url=ssh://${TARGET}:${TARGET_PORT} install "pdinstall_${RELEASE_SNAPPY_VERSION}_all.snap"
    rm *.snap

    exit
}

# If there is a failed install of paradrop, we need to clean up the files that are still around
# in order to attempt a second install
uninstall() {
    ssh -p ${TARGET_PORT} ${TARGET} sudo snappy remove pdinstall
    ssh -p ${TARGET_PORT} ${TARGET} sudo snappy remove paradrop
    ssh -p ${TARGET_PORT} ${TARGET} sudo rm -rf /writable/system-data/var/lib/apps/paradrop \
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

reboot() {
    if [ $ENVIRONMENT = "virtual" ]; then
        if [ ! -f pid.txt ]; then
            echo "No Snappy virtual machine running. Try:"
            echo -e "$0 up"
            exit
        fi
    fi
    echo -e "${COLOR} Rebooting the ${ENVIRONMENT} machine" && tput sgr0
    ssh -p ${TARGET_PORT} ${TARGET} sudo reboot
}

connect() {
    echo -e "${COLOR} SSH Connecting to the ${ENVIRONMENT} machine. user: ubuntu password: ubuntu" && tput sgr0
    ssh -p ${TARGET_PORT} ${TARGET}
}

check() {
    if [ $ENVIRONMENT = "virtual" ]; then
        if [ ! -f pid.txt ]; then
            echo "No Snappy virtual machine running. Try:"
            echo -e "$0 up"
            exit 1
        fi

        PID=`cat pid.txt`
        if [[ `ps -a | grep -E "^ *${PID}.*" | wc -l` -ne 1 ]]; then
            echo -e "Virtual machine is: DOWN\t\tPID: ${PID}"
            exit 1
        else
            echo "Virtual machine is: UP"
        fi
    fi
    ssh -p ${TARGET_PORT} ${TARGET} systemctl status paradrop_pd_*.service
}


logs() {
    if [ $ENVIRONMENT = "virtual" ]; then
        if [ ! -f pid.txt ]; then
            echo "No Snappy virtual machine running. Try:"
            echo -e "$0 up"
            exit 1
        fi
    fi

    ssh -p ${TARGET_PORT} ${TARGET} sudo /apps/paradrop/current/bin/dump_log.py
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
    "build") build;;
    # "clean") clean;;
    "run") run;;
    "install_deps") install_deps;;
    "install_dev") install_dev;;
    "install") install;;
    "uninstall") uninstall;;
    "setup") setup;;
    "up") up "$2";;
    "down") down;;
    "connect") connect;;
    "reboot") reboot;;
    "check") check;;
    "docs") docs;;
    "logs") logs;;
    "update-tools") update-tools;;
    "bui") build
        uninstall
        install_dev;;
    *) echo "Unknown input $1"
   ;;
esac
