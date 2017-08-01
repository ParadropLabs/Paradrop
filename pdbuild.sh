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
    echo -e "  build\t\t build snap"
    echo -e "  image\t\t build disk image"
    echo -e "  test\t\t run unit tests"
    echo -e "  docs\t\t rebuilds sphinx docs for readthedocs"
    echo -e "  version [version]\t\t get or set Paradrop version"
    echo -e "  release <version>\t\t prepare a version for release"
    exit
}

version() {
    if [ -n "$1" ]; then
        majmin=$(echo $1 | grep -oE "[0-9]+\.[0-9]+")
        sed -i "s/^version:.*/version: $1/" -i paradrop/snap/snapcraft.yaml
        sed -i "s/version=.*,/version='$1',/" -i paradrop/daemon/setup.py
        sed -i "s/version=.*,/version='$1',/" -i tools/setup.py
        sed -i "s/version =.*/version = \"$majmin\"/" -i docs/conf.py
        sed -i "s/release =.*/release = \"$1\"/" -i docs/conf.py
    else
        grep -oP "(?<=version: )\d+\.\d+\.\d+" paradrop/snap/snapcraft.yaml
    fi
}

release() {
    if [ -z "$1" ]; then
        printhelp
        exit 1
    fi

    git diff-index --quiet HEAD --
    if [ $? -ne 0 ]; then
        echo "The working tree is not clean."
        echo "You should commit your changes or clean up before releasing."
        exit 1
    fi

    branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$branch" != "master" ]; then
        echo "Not on the master branch."
        exit 1
    fi

    version $1

    git add --update
    git commit -m "Set version $1"

    git tag -a "v$1" -m "Release version $1"
}

activate_virtual_env() {
    . buildenv/env/bin/activate
}

deactivate_virtual_env() {
    deactivate
}

setup() {
    echo -e "${COLOR}Setting up virtualenv" && tput sgr0
    if [ ! -f /usr/local/bin/virtualenv ] && [ ! -f /usr/bin/virtualenv ]; then
        sudo apt-get install python-setuptools python-dev build-essential libcurl4-gnutls-dev libghc-gnutls-dev libffi-dev libssl-dev virtualenv
        sudo easy_install pip
    fi

    if ! type "snapcraft" > /dev/null; then
        echo -e "${COLOR} Installing snappy tools" && tput sgr0
        sudo apt-get update
        sudo apt-get install snapcraft
    fi

    echo -e "${COLOR}Snappy development tools installed" && tput sgr0

    virtualenv buildenv/env
    activate_virtual_env
    pip install -r requirements.txt
    deactivate_virtual_env
}

build() {
    # Set the build number if this is a CI build.
    if [ -n "$CI_JOB_ID" ]; then
        semver=$(version)
        version $semver+$CI_JOB_ID
    fi

    (cd paradrop; snapcraft clean; snapcraft)
}

image() {
    image="paradrop-amd64.img"

    if [ -e "$image" ]; then
        echo "Output file $image already exists."
        echo "Remove it before building a new image."
        exit 1
    fi

    echo "Select the paradrop-daemon snap to use (1 for snap store):"
    select pdsnap in paradrop-daemon paradrop/*.snap;
    do
        break
    done

    echo "Select the channel to track for paradrop-daemon:"
    select channel in stable candidate beta edge;
    do
        break
    done

    echo "Select the channel to track for all other snaps (recommended: stable):"
    select other_channel in stable candidate beta edge;
    do
        break
    done

    sudo ubuntu-image -o $image \
        --channel "$other_channel" \
        --extra-snaps "$pdsnap" \
        --image-size 4G \
        assertions/paradrop-amd64.model

    # The ubuntu-image command only takes a single channel argument and applies
    # it to all snaps.  If we we want to use a different channel for
    # paradrop-daemon, we can mount the image and modify seed.yaml.
    if [ "$channel" != "$other_channel" ]; then
        sudo mkdir -p /mnt/paradrop-amd64
        sudo mount -o loop,offset=$((106496*512)) $image /mnt/paradrop-amd64
        sudo python utils/set_seed_channel.py /mnt/paradrop-amd64/system-data/var/lib/snapd/seed/seed.yaml paradrop-daemon $channel
        sudo umount /mnt/paradrop-amd64
        sudo rmdir /mnt/paradrop-amd64
    fi

    echo "Created image $image, compressing..."
    xz --force --keep --compress $image
}

test() {
    activate_virtual_env
    nosetests -v
    deactivate_virtual_env
}

docs() {
    activate_virtual_env
    rm docs/requirements.txt
    pip install -e ./paradrop/daemon
    pip freeze | grep -v 'paradrop' > docs/requirements.txt
    deactivate_virtual_env
}

clean() {
    echo "Cleaning build directories"
    (cd paradrop; snapcraft clean)
    find . -name "*.pyc" | xargs rm -f
}

run() {
    echo -e "${COLOR}Starting Paradrop" && tput sgr0
    activate_virtual_env
    pip install -e ./paradrop/src
    sudo buildenv/env/bin/paradrop -m local -p $PWD/paradrop/localweb/www
    deactivate_virtual_env
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
    "image") image;;
    "clean") clean;;
    "run") run;;
    "docs") docs;;
    "version") version $2;;
    "release") release $2;;
    *) echo "Unknown input $1"
   ;;
esac
