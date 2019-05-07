PC Engines APU2
===============

Hardware requirements
---------------------

* 1x system board (`apu2c4 <http://pcengines.ch/apu2c4.htm>`_)
* 1x case (`case1d2u <http://pcengines.ch/case1d2u.htm>`_ for two antennas or `case1d2redu6 <https://pcengines.ch/case1d2redu6.htm>`_ for up to six antennas)
* 1-2x miniPCIe Wi-Fi modules (`wle200nx <http://pcengines.ch/wle200nx.htm>`_ for 802.11n or `wle600vx <http://pcengines.ch/wle600vx.htm>`_ for 802.11ac)
* 2-4x pigtails (`pigsma <http://pcengines.ch/pigsma.htm>`_)
* 2-4x antennas (`antsmadb <http://pcengines.ch/antsmadb.htm>`_)
* 1x power supply (`ac12vus2 <http://pcengines.ch/ac12vus2.htm>`_)
* 1x storage module (`sd4b <http://pcengines.ch/sd4b.htm>`_) or alternative (see below)

All of these parts are available internationally from
`PC Engines <https://pcengines.ch/order.htm>`_.

Storage Module
--------------

The APU can boot from an SD card or an m-SATA SSD.  These instructions
are written assuming you will use an SD card because they are easier to
flash from another machine.  However, we do frequently build Paradrop
routers with SSDs to take advantage of the higher storage capacity and
read/write speeds.  The 4GB pSLC module listed above is known to be very
reliable, but you may also prefer a larger SD card.

Preparing the SD card
---------------------

1. Download the latest build of the Paradrop
   `disk image <https://paradrop.org/release/latest/paradrop-amd64.img.xz>`_
2. Insert the SD card into the machine you used to download the image and find
   the device node for the card.  This is often "/dev/sdb", but please make
   sure, as the next command will overwrite the contents of whatever device you
   pass.
3. Copy ("flash") the Paradrop image to the SD card.::

    xzcat paradrop-amd64.img.xz | sudo dd of=<DEVICE> bs=32M status=progress; sync

4. Remove the SD card and proceed to assemble the router.

Please note that in order to make the SD card bootable, it is not
enough to copy the disk image file to an existing filesystem on
the SD card. Instead, one must overwrite the contents of the SD
card including MBR, partition table, and data with the provided
disk image.  In Linux, you can do this with the `dd` command. If
you are using Windows, we suggest using the `win32-image-writer
<https://launchpad.net/win32-image-writer>`_ tool. Follow the
Sourceforge link to download the installer.

Connecting to the Serial Console
--------------------------------

If you know the IP address of the router, e.g. because you have access
to the DHCP server upstream from the router, then you can skip this
step and proceed with the steps for activating and using your router
described in the section :doc:`../manual/index`.

If you do not have network access to the Paradrop router for any reason,
you can always connect a serial cable to the 9-pin serial port. The
default configuration is 9600 8N1. If you are using PuTTY under Windows,
make sure that you have entered the correct COM port for your serial
cable. It may not be "COM1". You can use the `chgport` command or open
the Windows Device Manager tool to find the correct COM port.
At the login prompt, the default username is "paradrop" with no
password.
