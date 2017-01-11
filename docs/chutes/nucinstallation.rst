Installing on the Intel NUC
===========================

These instructions will help you install the ParaDrop daemon on the Intel NUC platform.  At the end of this process, you will have a system ready for installing chutes.

We have specifically tested this process on the Skull Canyon (NUC6i7KYK) platform, which we recommend for high performance edge-computing needs.

Hardware and software requirements
----------------------------------

* Intel NUC Skull Canyon NUC6i7KYK
   * The Intel NUC devices generally do not come with memory or storage pre-installed.
   * Memory: we recommend at least one 8 GB DDR4 SODIMM.
   * Storage: we have generally found one 16 GB SD card to be sufficient for our storage needs, but we recommend using one MX300 M.2 SSD card for the higher read and write speeds.
   * We recommend updating the BIOS on the NUC.  Follow the instructions on `the Intel support site <http://www.intel.com/content/www/us/en/support/boards-and-kits/000005850.html>`_.
* 2 USB 2.0 or 3.0 flash drives (each 4 GB minimum)
* A monitor with an HDMI interface
* A network connection with Internet access
* An `Ubuntu Desktop 16.04.1 LTS image <http://releases.ubuntu.com/16.04.1/ubuntu-16.04.1-desktop-amd64.iso>`_.
* A `ParaDrop disk image <https://paradrop.org/release/2017-01-09/paradrop_router.img.gz>`_.

Preparing for installation
--------------------------

1. Download the Ubuntu Desktop image and prepare a bootable USB flash drive.
2. Download the ParaDrop disk image and copy the file to the second flash drive.

Boot from the Live USB flash drive
----------------------------------

1. Insert the Live USB Ubuntu Desktop flash drive in the NUC.
2. Start the NUC and push F10 to enter the boot menu.
3. Select the USB flash drive as a boot option.
4. Select "Try Ubuntu without installing".

Flash ParaDrop
--------------

1. Once the system is ready, insert the second USB flash drive which contains the ParaDrop disk image.
2. Open a terminal and run the following command, where <disk label> is the name of the second USB flash drive.  You may wish to double-check that /dev/sda is the desired destination **before running dd**. ::

    zcat /media/ubuntu/<disk label>/paradrop_router.img.gz | sudo dd of=/dev/sda bs=32M status=progress; sync
3. Reboot the system and remove all USB flash drives when prompted to do so.

First boot
----------

1. At the Grub menu, press 'e' to edit the boot options.
2. Find the line that begins with "linux" and append the option "nomodeset".  It should look like "linux (loop)/kernel.img $cmdline nomodeset".  Adding this option will temporarily fix a graphics issue that is known to occur with the Intel NUC.
3. Press F10 to continue booting.
4. Press Enter when prompted, and follow the instructions on the screen to configure Ubuntu Core.  If you have an Ubuntu One account.  By connecting your Ubuntu One account, you will be able to login via SSH with the key(s) attached to your account.  Otherwise, if you do not have an Ubuntu One account or do not wish to use it, you may enter "info@paradrop.io" as your email address.  You will still be able to manage your router and install chutes through paradrop.org either way.
5. Take note of the IP address displayed on the screen.  You will need this address for the next step, activating the router.  For example, the message below indicates that the router has IP address 10.42.0.162. ::

    Congratulations! This device is now registered to info@paradrop.io.

    The next step is to log into the device via ssh:

    ssh paradrop@10.42.0.162
    ...

Activate the Router
-------------------

Follow these steps the first time you start a new physical or virtual ParaDrop router.  Activation associates the router with your account on `paradrop.org <https://paradrop.org>`_ so that you can manage the router and install chutes from the chute store.

1. Make an account on `paradrop.org <https://paradrop.org>`_ if you do not have one.
2. From the Routers tab, click Create Router.  Give your router a unique name and an optional description to help you remember it and click Submit.
3. On the router page, find the "Router ID" and "Password" fields.  You will need to copy this information to the router so that it can connect.
4. Open the router portal at http://<router_address>.  Click the "Activate the router with a ParaDrop Router ID" button and enter the information from the paradrop.org router page.  If the activation was successful, you should see checkmarks appear on the "WAMP Router" and "ParaDrop Server" lines.  You may need to refresh the page to see the update.
