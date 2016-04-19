#!/bin/bash

# Include common functions and defines for both local and remote
source pdcommon.sh

# Include the remote address of the device
source pdremote.conf

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
    echo -e "  install \t get official snaps and install on the remote machine."
    echo -e "  install_dev \t build the paradrop snaps and install on the remote machine."
    echo -e "  uninstall \t removes paradrop on the remote machine."
    echo -e "  setup\t\t prepares environment for snappy testing"
    echo -e "  reboot\t\t reboots the hardware properly"
    echo -e "  connect\t connects to the snappy machine"
    echo -e "  check\t\t checks the state of the Paradrop instance tools in the device"
    echo -e "  logs\t\t print out the logs from in the machine directly to screen (only use to debug issues)"

    echo -e "\nDevelopment operations"
    echo -e "  docs\t\t rebuilds sphinx docs for readthedocs"
    echo -e "  update-tools\t uploads build tools to pypi. Requires authentication."
    exit
}

#Show help if no args passed
if [ $# -lt 1 ]
then
    printhelp
fi

#############
# Utils
###
removekey() {
    ssh-keygen -f "~/.ssh/known_hosts" -R ${TARGET}
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

###
# Call Operations
###

case "$1" in
    "help") printhelp;;
    "--help") printhelp;;
    # "clean") clean;;
    "install_deps") install_deps;;
    "install") install;;
    "uninstall") uninstall;;
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
