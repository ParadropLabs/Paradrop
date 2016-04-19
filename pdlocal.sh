#!/bin/bash

# Include common functions and defines for both local and remote
source pdcommon.sh

#############
# Static defines
###

TARGET="ubuntu@localhost"
TARGET_PORT="8022"

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
    echo -e "  install \t compile snap and install on local snappy virtual machine."
    echo -e "  uninstall \t removes paradrop from the local vm"
    echo -e "  setup\t\t prepares environment for local snappy testing"
    echo -e "  up\t\t starts a local snappy virtual machine, add wifi interface with 'up wifi-BUS-ADDR'"
    echo -e "  down\t\t closes a local snappy virtual machine"
    echo -e "  reboot\t\t reboots the VM properly"
    echo -e "  connect\t connects to a local snappy virtual machine"
    echo -e "  check\t\t checks the state of the VM and Paradrop instance tools in the VM"
    echo -e "  logs\t\t print out the logs from in the VM directly to screen (only use to debug issues)"

    echo -e "\nDevelopment operations"
    echo -e "  docs\t\t rebuilds sphinx docs for readthedocs"
    echo -e "  update-tools\t uploads build tools to pypi. Requires authentication."
    exit
}

# Check for no parameters passed and print help
if [ $# -lt 1 ]
then
    printhelp
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

removekey() {
    # Remove the localhost key if they started a different image
    echo -e 'Removing old ssh key pair'
    ssh-keygen -f "~/.ssh/known_hosts" -R [localhost]:8022
}

# Perhaps overkill, but preps the local environment for snappy testing
setup() {
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

    if ! type "snappy" > /dev/null; then
        echo -e "${COLOR} Installing snappy tools" && tput sgr0
        sudo add-apt-repository ppa:snappy-dev/tools
        sudo apt-get update
        sudo apt-get install snappy-tools bzr
    fi

    echo -e "${COLOR}Snappy development tools installed" && tput sgr0
}

#############
# Operations
###

up() {
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
}

down() {
    killvm
}

reboot() {
    if [ ! -f pid.txt ]; then
        echo "No Snappy virtual machine running. Try:"
        echo -e "$0 up"
        exit
    fi

    echo -e "${COLOR} Rebooting the VM" && tput sgr0
    ssh -p 8022 ubuntu@localhost sudo reboot
}

connect() {
    if [ ! -f pid.txt ]; then
        echo "No Snappy virtual machine running. Try:"
        echo -e "$0 up"
        exit
    fi

    echo -e "${COLOR} Connecting to virtual machine. user: ubuntu password: ubuntu" && tput sgr0
    ssh -p 8022 ubuntu@localhost
}

check() {
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

    ssh -p 8022 ubuntu@localhost systemctl status paradrop_pd_*.service
}

logs() {
    if [ ! -f pid.txt ]; then
        echo "No Snappy virtual machine running. Try:"
        echo -e "$0 up"
        exit 1
    fi

    ssh -p 8022 ubuntu@localhost sudo /apps/paradrop/current/bin/dump_log.py
}

##########
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
    *) echo "Unknown input $1"
   ;;
esac
