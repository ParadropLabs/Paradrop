Virtual Machine
===============

This will quickly take you through the process of bringing up a Hello World chute in a virtual machine on your computer.

*NOTE*: These instructions assume you are running Ubuntu.  The steps to launch a virtual machine may be different for other environments.


Environment setup
-----------------

These steps wil download our router image and launch it a virtual machine.

1. Install required packages::

    sudo apt-get install qemu-kvm

2. Download the latest build of the Paradrop disk image.  https://paradrop.org/release/|version|/paradrop-amd64.img.xz
3. Extract the image::

    xz -d paradrop-amd64.img.xz

4. Launch the VM::

    sudo kvm -m 1024 \
    -netdev user,id=net0,hostfwd=tcp::8000-:8000,hostfwd=tcp::8022-:22,hostfwd=tcp::8080-:80 \
    -device virtio-net-pci,netdev=net0 -drive file=paradrop-amd64.img,format=raw


First Boot Setup
----------------

After starting the virtual machine for the first time, follow the instructions on the screen.  When it prompts for an email address, enter `info@paradrop.io`.  This sets up a user account on the router called `paradrop` and prepares the router to receive software upgrades.  Allow the router 1-2 minutes to complete its setup before proceeding.

Please note: there is no username/password to log into the system console.  Please follow the steps in the next sections to access your router through paradrop.org or through SSH.


Activating your Router
----------------------

Follow these steps the first time you start a new physical or virtual Paradrop router.  Activation associates the router with your account on `paradrop.org <https://paradrop.org>`_ so that you can manage the router and install chutes from the chute store.

1. Make an account on `paradrop.org <https://paradrop.org>`_ if you do not have one.
2. From the Routers tab, click Create Router.  Give your router a unique name and an optional description to help you remember it and click Submit.
3. On the router page, find the "Router ID" and "Password" fields.  You will need to copy this information to the router so that it can connect.
4. Open the router portal at `http://localhost:8080 <http://localhost:8080>`_.  If you are prompted to login, the default username is `paradrop` with an empty password.  Click the "Activate the router witha ParaDrop Router ID" button and enter the information from the paradrop.org router page.  If the activation was successful, you should see checkmarks appear on the "WAMP Router" and "ParaDrop Server" lines.  You may need to refresh the page to see the update.


Installing Chutes
-----------------

1. Make an account on `paradrop.org <https://paradrop.org>`_ and make sure you have an activated, online router.
2. Go to the Chute Store tab on paradrop.org.  There you will find some public chutes such as the hello-world chute.  You can also create your own chutes here.
3. Click on the hello-world chute,  click Install, click your router's name to select it, and finally, click Install.
4. That will take you to the router page again where you can click the update item to monitor its progress.  When the installation is complete, an entry will appear under the Chutes list.
5. The hello-world chute starts a webserver, which is accessible at `http://localhost:8000 <http://localhost:8000>`_.  Once the installation is complete, test it in a web browser.


Connecting to your Router with SSH
----------------------------------

The router is running an SSH server, which is forwarded from localhost port 8022 with the kvm command above.  The router does not accept password login by default, so you will need to have an RSA key pair available, and you can use the router configuration page to upload the public key and authorize it.

1. Open tools page on the router (`http://localhost:8080/#!/tools <http://localhost:8080/#!/tools>`_).
2. Find the SSH Keys section and use the text area to submit your public key.  Typically, your public key file will be found at `~/.ssh/id_rsa.pub`.  You can use `ssh-keygen` to generate one if you do not already have one.  Copy the text from the file, and make sure the format resembles the example before submitting.
3. After the key has been accepted by the router, you can login with the command `ssh -p 8022 paradrop@localhost`.  The username may be something other than paradrop if you used your own Ubuntu One account instead of info@paradrop.io during the First Boot Setup.
