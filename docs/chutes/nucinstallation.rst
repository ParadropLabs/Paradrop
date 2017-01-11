Installing on the Intel NUC
===========================

These instructions will help you install the ParaDrop daemon on the Intel NUC platform.  At the end of this process, you will have a system ready for installing chutes.

We have specifically tested this process on the Skull Canyon (NUC6i7KYK) platform, which we recommend for high performance edge-computing needs.

Hardware and software requirements
----------------------------------

* Intel NUC Skull Canyon NUC6i7KYK
  * The Intel NUC devices generally do not come with memory or storage pre-installed.
  * Memory: we recommend at least one 8 GB DDR4 SODIMM.
  * Storage: we have generally found one 16 GB SD card to be sufficient for our storage needs, but we recommend using one MX300 M.2 SSD card for the higher read-write speeds.
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

Activate the Router
-------------------

Follow these steps the first time you start a new physical or virtual ParaDrop router.  Activation associates the router with your account on `paradrop.org <https://paradrop.org>`_ so that you can manage the router and install chutes from the chute store.

1. Make an account on `paradrop.org <https://paradrop.org>`_ if you do not have one.
2. From the Routers tab, click Create Router.  Give your router a unique name and an optional description to help you remember it and click Submit.
3. On the router page, find the "Router ID" and "Password" fields.  You will need to copy this information to the router so that it can connect.
4. The next step is to find the IP address of your router.  Either find the IP address of the WAN interface or connect to the router's WiFi network, in which case it will be 192.168.1.1.
5. Open the router portal at http://<router_address>.  Click the "Activate the router with a ParaDrop Router ID" button and enter the information from the paradrop.org router page.  If the activation was successful, you should see checkmarks appear on the "WAMP Router" and "ParaDrop Server" lines.  You may need to refresh the page to see the update.
