NVIDIA Jetson TX2
=================

Hardware requirements
---------------------

* Jetson TX2 Developer Kit
* USB camera - the Logitech C615 is known to work well.

Preparing the Board
-------------------

The first step in setting up the hardware is to use the NVIDIA SDK tools
from a separate computer to flash the Jetson board and install drivers.

1. Download and install the `Nvidia SDK manager <https://developer.nvidia.com/nvidia-sdk-manager>`.
   The download may require creating a free Nvidia developer account.
   These instructions were tested with SDK Manager version 0.9.14.4961.
2. Follow the instructions to flash the latest version of Jetpack on the board.
   These instructions were tested with Jetpack 4.2.2.
3. Install the optional Jetson SDK components on the target device.
   In particular, be sure to install the NVIDIA Container Runtime.

Tensorflow Base Images
----------------------

Next, we will set up some base images on the Jetson board. You can either
login via SSH or use a monitor and keyboard connected to the Jetson board.
These base images can be shared by multiple applications.

1. `git clone https://github.com/cara/cogwerx-jetson-tx2.git && cd cogwerx-jetson-tx2`
2. `sudo docker build -f Dockerfile.cudabase -t openhorizon/aarch64-tx2-cudabase .`
3. `sudo docker build -f darknet/Dockerfile.darknet-tx2 -t openhorizon/aarch64-tx2-darknet darknet`

Installing the Paradrop Agent
-----------------------------

We will also want to install the Paradrop agent. This is what will
allow us to remotely manage the edge services that run on the Jetson
board. The easiest way to install Paradrop will be from PyPI.

1. `sudo apt install haproxy libcurl4-openssl-dev libffi-dev libssl-dev python-pip`
2. `sudo pip install paradrop`
3. `sudo paradrop & disown #1`

Note: you will need to re-run the last command any time you reboot the
Jetson board.  A more permanent installation should use a systemd unit
file to start the Paradrop agent automatically.

Installing an Example Application
---------------------------------

Finally, we are ready to install an edge service on the node.  Find the
IP address of your Jetson board, which you may have used earlier during
the setup process. On the same machine that you ran the NVIDIA SDK tools
or on another machine connected to the local network, you can use pdtools
commands to install a chute on the node.

1. If you have not already, install pdtools.

   `sudo pip install pdtools`

2. Set the PDTOOLS_NODE_TARGET environment variable to the IP address of your node. Substitute your node's IP address in the command below.

   `export PDTOOLS_NODE_TARGET=192.168.1.167`.

3. `git clone https://github.com/ParadropLabs/jetson-example-darknet.git && cd jetson-example-darknet`
4. `pdtools node install-chute`.
4. Visit the web page installed by the chute by substituting your node IP address in the link below.

   http://192.168.1.167/chutes/jetson-example-darknet
