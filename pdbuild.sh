#!/bin/bash 

#used to differentiate our output from other. Other output is still shown 
# in the case of errors
COLOR='\033[01;33m' 

#Show help if no args passed
if [ $# -lt 1 ]
then
    echo -e "${COLOR}Paradrop build tools." && tput sgr0
    echo -e "This tool installs all needed dependencies in a local virtual environment and can set up Snappy development\n"

    echo -e "To get paradrop on a snappy instance as quickly as possible, run build and install\n"

    echo "Usage:"
    echo -e "  build\n\t build and package dependencies, install paradrop locally"
    echo -e "  clean\n\t remove virtual environment, clean packages"
    echo -e "  run\n\t run paradrop locally"
    echo -e "  install \n\t compile snap and install on local snappy virtual machine."
    echo -e "  setup\n\t prepares environment for local snappy testing"
    echo -e "  up\n\t starts a local snappy virtual machine"
    echo -e "  down\n\t closes a local snappy virtual machine"
    echo -e "  connect\n\t connects to a local snappy virtual machine"

    exit
fi


###
# Utils
###
killvm() {
    if [ -f buildenv/pid.txt ]; then
        echo -e "${COLOR}Killing snappy virtual machine" && tput sgr0
        KVM="$(cat buildenv/pid.txt)"
        kill "${KVM}"
        rm buildenv/pid.txt
    else
        echo -e "${COLOR}Snappy virtual machine is not running" && tput sgr0
    fi
}

###
# Operations
###

# venv.pex is a bootstrapped virtualenv. It allows us to install without requiring the 
# package to be installed on a local system. After creating the environment, installs 
# paradrop and its dependancies, then bundles them into a pex and sets it in the bin directory
build() {
    echo -e "${COLOR}Loading and building python dependencies"
    echo -e "${COLOR}Bootstrapping environment" && tput sgr0

    ./venv.pex buildenv/env
    source buildenv/env/bin/activate

    echo -e "${COLOR}Installing paradrop" && tput sgr0

    pip install pex
    pip install -e ./paradrop

    #also-- we can get away without saving the requirements just fine, but readthedocs needs them
    pip freeze | grep -v 'pex' | grep -v 'paradrop' > docs/requirements.txt
    # pex -r docs/requirements.txt -o snap/bin/pd.pex -m paradrop.main:main -f buildenv/dist

    #the above is somewhat redundant now, but meh
    cd buildenv
    python ../paradrop/setup.py bdist_egg -d .
    cd ..

    echo -e "${COLOR}Building paradrop-snappy..." && tput sgr0
    pex paradrop -o snap/bin/pd.pex -m paradrop:main -f buildenv/
    rm -rf *.egg-info
}

clean() {
    echo "Cleaning build directories"

    rm -rf buildenv
    # rm -rf src/paradrop.egg-info
    rm snap/bin/pd.pex
}

run() {
    echo -e "${COLOR}Starting Paradrop" && tput sgr0

    if [ ! -f snap/bin/pd.pex ]; then
        echo "Dependency pex not found! Have you built the dependencies yet?"
        echo -e "\t$ $0 build"
        exit
    fi

    snap/bin/pd.pex
}

install() {
    if [ ! -f snap/bin/pd.pex ]; then
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

    echo -e "${COLOR}Building snap" && tput sgr0

    
    
    #build the snap using snappy dev tools and extract the name of the snap
    snappy build snap
    SNAP=$(ls | grep ".snap")

    echo -e "${COLOR}Installing snap" && tput sgr0
    snappy-remote --url=ssh://localhost:8022 install "${SNAP}"
    rm *.snap
    
    exit
}

# Perhaps overkill, but preps the local environment for snappy testing
setup() {
    if ! type "kvm" > /dev/null; then
        echo -e '${COLOR}Installing kvm' && tput sgr0
        sudo apt-get install qemu-kvm -y
    fi

    #check for image only download if it does not already exist
    if [ ! -f buildenv/ubuntu-15.04-snappy-amd64-generic.img ]; then
        echo -e "${COLOR}Downloading Snappy image." && tput sgr0

        if ! [ -d "./buildenv" ]; then
            mkdir buildenv
        fi

        #cd because the -p flag to wget acted up 
        wget http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz 
        unxz ubuntu-15.04-snappy-amd64-generic.img.xz
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

up() {
    if [ -f buildenv/pid.txt ]; then
        echo "Snappy virtual machine is already running. If you believe this to be an error, try:"
        echo -e "$0 down"
        exit
    fi

    if [ ! -f ubuntu-15.04-snappy-amd64-generic.img ]; then
        echo "Snappy image not found. Try:"
        echo -e "\t$0 setup"
        exit
    fi

    echo "Starting snappy instance on local ssh port 8022."
    echo "Please wait for the virtual machine to load."
    kvm -m 512 -redir :8090::80 -redir :8022::22 -redir :8777::7777 -redir :9999::14321 ubuntu-15.04-snappy-amd64-generic.img &
    echo $! > buildenv/pid.txt
}

down() {
    killvm
}

connect() {
    if [ ! -f buildenv/pid.txt ]; then
        echo "No Snappy virtual machine running. Try:"
        echo -e "$0 up"
    fi

    echo -e "${COLOR} Connecting to virtual machine. user: ubuntu password: ubuntu" && tput sgr0
    ssh -p 8022 ubuntu@localhost
}

###
# Call Operations
###

case "$1" in
    "build") build;;
    "clean") clean;;
    "run") run;;
    "install") install;;
    "setup") setup;;
    "up") up;;
    "down") down;;
    "connect") connect;;
    *) echo "Unknown input $1"
   ;;
esac
