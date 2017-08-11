Virtual Machine
===============

This will quickly take you through the process of bringing up a Hello World chute in a virtual machine on your computer.

*NOTE*: These instructions assume you are running Ubuntu.  The steps to launch a virtual machine may be different for other environments.


Environment setup
-----------------

These steps wil download our router image and launch it a virtual machine.

1. Install required packages::

    sudo apt-get install qemu-kvm

2. Download the latest build of the Paradrop disk image. `<https://paradrop.org/release/latest/paradrop-amd64.img.xz>`_
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


Connecting to your Router with SSH
----------------------------------

The router is running an SSH server, which is forwarded from localhost port 8022 with the kvm command above.  The router does not accept password login by default, so you will need to have an RSA key pair available, and you can use the router configuration page to upload the public key and authorize it.

1. Open tools page on the router (`http://localhost:8080/#!/tools <http://localhost:8080/#!/tools>`_).
2. Find the SSH Keys section and use the text area to submit your public key.  Typically, your public key file will be found at `~/.ssh/id_rsa.pub`.  You can use `ssh-keygen` to generate one if you do not already have one.  Copy the text from the file, and make sure the format resembles the example before submitting.
3. After the key has been accepted by the router, you can login with the command `ssh -p 8022 paradrop@localhost`.  The username may be something other than paradrop if you used your own Ubuntu One account instead of info@paradrop.io during the First Boot Setup.


Managing Virtual Machines Using virt-manager
--------------------------------------------

Even though many developers prefer command line tools to manage virtual machines, some developers likes to use GUI tools.
In addition, GUI tools are convenient to support some advanced features,
e.g., assigning some peripheral devices (USB WiFi dongle) from host to virtual machines.
We recommend using "virt-manager" to run ParaDrop virtual machines.
If you have not installed it on Ubuntu, you can use below command to install it::

    sudo apt-get install virt-manager

Then we can start virt-manager with below command::

    sudo virt-manager

We can create a VM with the ParaDrop disk image.

  .. image:: ../images/create_vm.png
    :align:  center

Below is the configuration of the VM.

  .. image:: ../images/create_vm_final.png
    :align:  center

After that, we can boot the VM and configure the first boot as we do when run the VM with command line tools.
However, the VM will have an IP address 192.168.122.x, so we can access http://<IP address of the VM> to access the portal
to upload ssh keys, and then login to it directly with the IP address.

We can assign the USB WiFi dongle from the Host to the ParaDrop VM so that the ParaDrop running on the VM can support features related to WiFi.
Before we do that, we need to disable the WiFi device for Host.
We can do that with "rflist" command.
Run below command to get the number of the WiFi device::

  rflist list

Suppose the number of the WiFi device we want to assign to the ParaDrop VM is 2, then run below command to disable it for host OS::

  rflist block 2

Then we can add the USB WiFi dongle to the VM.

  .. image:: ../images/add_usb_wifi_to_vm.png
    :align:  center

We can run below command in ParaDrop VM to verify that the WiFi device has been detected::

  iw dev

Sometimes, we have to repeat above steps to make sure the WiFi device can be used by the ParaDrop VM.
