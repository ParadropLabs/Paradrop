Intel NUC
=========

These instructions will help you install the ParaDrop daemon on the Intel NUC
platform.  At the end of this process, you will have a system ready for
installing chutes.

We have specifically tested this process on the Skull Canyon (NUC6i7KYK)
platform, which we recommend for high performance edge-computing needs.

Hardware and software requirements
----------------------------------

* Intel NUC Skull Canyon NUC6i7KYK
   * The Intel NUC devices generally do not come with memory or storage pre-installed.
   * Memory: we recommend at least one 8 GB DDR4 SODIMM.
   * Storage: we have generally found one 16 GB SD card to be sufficient for
     our storage needs, but we recommend using one MX300 M.2 SSD card for the
     higher read and write speeds.
   * We recommend updating the BIOS on the NUC.  Follow the instructions on
     `the Intel support site
     <http://www.intel.com/content/www/us/en/support/boards-and-kits/000005850.html>`_.
* 2 USB 2.0 or 3.0 flash drives (each 4 GB minimum)
* A monitor with an HDMI interface
* A network connection with Internet access
* An `Ubuntu Desktop 16.04.1 LTS image
  <http://releases.ubuntu.com/16.04.1/ubuntu-16.04.1-desktop-amd64.iso>`_.
* A `ParaDrop disk image
  <https://paradrop.org/release/latest/paradrop-amd64.img.xz>`_.

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

1. Once the system is ready, insert the second USB flash drive which contains
   the ParaDrop disk image.
2. Open a terminal and run the following command, where <disk label> is the
   name of the second USB flash drive.  We recommend that you double-check that
   /dev/sda is the desired destination **before running dd**. ::

    xzcat /media/ubuntu/<disk label>/paradrop_router.img.xz | sudo dd of=/dev/sda bs=32M status=progress; sync
3. Reboot the system and remove all USB flash drives when prompted to do so.

First boot
----------

1. At the Grub menu, press 'e' to edit the boot options.
2. Find the line that begins with "linux" and append the option "nomodeset".
   It should look like "linux (loop)/kernel.img $cmdline nomodeset".  Adding
   this option will temporarily fix a graphics issue that is known to occur
   with the Intel NUC.
3. Press F10 to continue booting.
4. Please allow three to five minutes for the initialization to complete.
   During this time, the device will finish installing software packages
   and prepare the device to receive updates. After the setup is complete,
   a login prompt will appear. The default username is "paradrop" with
   no password.
5. Take note of the IP address displayed on the console. You may need to
   use this address to connect to the admin panel or use pdtools commands.
   For example, the console below indicates that the node has IP address
   10.42.0.162. ::

    Ubuntu Core 16 on 10.42.0.162 (tty1)

    localhost login:
