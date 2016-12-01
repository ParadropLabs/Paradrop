Getting Started
===============

This will quickly take you through the process of bringing up a Hello World chute in a virtual machine on your computer.

*NOTE*: These instructions assume you are running Ubuntu.  The steps to launch a virtual machine may be different for other environments.

Environment setup
-----------------

These steps wil download our router image and launch it a virtual machine.

1. Install required packages::

    sudo apt-get install qemu-kvm

2. Download the latest image (paradrop_router.img.tgz) from `our releases <https://paradrop.org/release/2016-11-08/>`_.
3. Extract the image::

    tar xf paradrop_router.img.tgz

4. Launch the VM::

    kvm -m 1024 \
    -netdev user,id=net0,hostfwd=tcp::8000-:8000,hostfwd=tcp::8022-:22,hostfwd=tcp::8080-:80,hostfwd=tcp::14321-:14321 \
    -device virtio-net-pci,netdev=net0 -drive file=paradrop_router.img,format=raw


Activating your Router
----------------------

Follow these steps the first time you start a new physical or virtual Paradrop router.  Activation associates the router with your account on `paradrop.org <https://paradrop.org>`_ so that you can manage the router and install chutes from the chute store.

1. Make an account on `paradrop.org <https://paradrop.org>`_ if you do not have one.
2. From the Routers tab, click Create Router.  Give your router a unique name and an optional description to help you remember it and click Submit.
3. On the router page, find the "Router ID" and "Password" fields.  You will need to copy this information to the router so that it can connect.
4. Open the router portal at `http://localhost:8080 <http://localhost:8080>`_.  Click the Login button and enter the information from the paradrop.org router page.  You may need to refresh the page before the messages appear.  **Important**: Although the Login button remains on the page, you only need to complete this step one time for a router.  If the activation was successful, you should see the following messages::

    This router is provisioned.
    The HTTP connection is ready.
    The WAMP connection is ready.

Installing Chutes
-----------------

1. Make an account on `paradrop.org <https://paradrop.org>`_ and make sure you have an activated, online router.
2. Go to the Chute Store tab on paradrop.org.  There you will find some public chutes such as the hello-world chute.  You can also create your own chutes here.
3. Click on the hello-world chute,  click Install, click your router's name to select it, and finally, click Install.
4. That will take you to the router page again where you can click the update item to monitor its progress.  When the installation is complete, an entry will appear under the Chutes list.
5. The hello-world chute starts a webserver, which is accessible at `http://localhost:8000 <http://localhost:8000>`_.  Once the installation is complete, test it in a web browser.
