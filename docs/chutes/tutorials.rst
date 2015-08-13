Paradrop Chute Tutorials
=============================

This page details out information about advanced chute architecture and installation.
We assume you have already gone through :doc:`gettingstarted`.


Testing on your development computer
-------------------------------------

To keep the development process for Paradrop as simple as possible, we heavily encourage and support developers testing their chutes on a virtual machine (VM).

Wi-Fi in virtual machines
"""""""""""""""""""""""""""""

In order to support development on a virtual machine, you most likely need a Wi-Fi device (otherwise it wouldn't be a router would it??).
The instructions below will show how to enable Wi-Fi specifically for USB adapters, but other internal Wi-Fi cards should follow similar steps.

Plug in the WiFi card, on Ubuntu, run ``lsusb``, you should see::

    Bus 002 Device 005: ID 148f:5372 Ralink Technology, Corp. RT5372 Wireless Adapter

Make note of the *Bus* and *Device* numbers, in this case 2 and 5.

When you go to launch your VM with a Wi-Fi device, simply run the command::

    sudo pdbuild.sh up wifi-2-5

You need ``sudo`` access because the VM needs to pull in the USB device, which is privileged. 

You can verify that the WiFi adapter is inside of the VM by running::

    pdbuild connect
    
    (amd64)ubuntu@localhost:~$ iw dev
    phy#0
        Interface wlan0
            ifindex 4
            wdev 0x1
            addr 7c:dd:90:8f:c2:5e
            type managed


This will SSH you into the VM and print out information about the WiFi adapter, if this print out is blank, also try ``iw phy`` which prints out physical information about the Wi-Fi radio.

Wi-Fi Enabled Chutes
-------------------------

Here we will describe how to install a chute that utilizes a WiFi radio in the router.

Chute: Virtual Router
-----------------------

The chute we will install is called *virtual router* it is as simple as it sounds.
This chute will setup a fully functional virtual router inside of the real router hardware (or VM).
This is useful to demonstrate the full capability of Paradrop, which will setup and establish the chute, and tie together the networking components needed to allow the chute to function as a router.

Setup:

* Make sure your VM is alive and has WiFi (explained above).
* Make sure you are logged in or registered using pdtools.

Install the chute::

    cd <example_apps>/virtual-router
    vim config.yaml
    #Setup ssid and password (defaults to "Paradrop-Network" and "ParadropRocks!")
    paradrop chute install localhost 9999 config.yaml
    
    ... (install output)
    Chute virtual-router create success

Now use your laptop or phone and search for the SSID you created, you should be able to associate to it and use it normally.
You can verify you are using the chute for internet by stopping it::

     paradrop chute stop localhost 9999 virtual-router
     Stopping chute...

     Chute virtual-router stop success


