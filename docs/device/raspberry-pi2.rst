Raspberry Pi 2
==============

Hardware requirements
---------------------

* 1x Raspberry Pi 2 (recommended: 1 GB memory)
* 1x micro SD card (minimum: 4 GB, recommended: 16 GB)

Preparing the SD card
---------------------

1. Download the latest build of the Paradrop
   `disk image <https://paradrop.org/release/latest/paradrop-pi2.img.xz>`_
2. Insert the SD card into the machine you used to download the image and find
   the device node for the card.  This is often "/dev/sdb", but please make
   sure, as the next command will overwrite the contents of whatever device you
   pass.
3. Copy ("flash") the Paradrop image to the SD card.::

    xzcat paradrop-pi2.img.xz | sudo dd of=<DEVICE> bs=32M status=progress; sync

4. Insert the SD card in the Raspberry Pi and proceed to power it.

Please note that in order to make the SD card bootable, it is not
enough to copy the disk image file to an existing filesystem on
the SD card. Instead, one must overwrite the contents of the SD
card including MBR, partition table, and data with the provided
disk image.  In Linux, you can do this with the `dd` command. If
you are using Windows, we suggest using the `win32-image-writer
<https://launchpad.net/win32-image-writer>`_ tool. Follow the
Sourceforge link to download the installer.

First Boot
----------

The first time you boot the target device, ensure that it is connected
to a wired network. Identify the IP address that the Raspberry Pi device
received from the network and proceed to the activation step described
in the section :doc:`../manual/index`.
