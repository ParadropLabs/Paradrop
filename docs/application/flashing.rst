
Flashing real hardware
---------------------------------

Check this page for instructions on flashing different types of hardware.


Flashing x86
----------------------------------

These instructions apply to x86 routers distributed by the Paradrop development team (PC Engines APU1 boards).

Download snappy here: `Ubuntu Snappy <http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz>`_

Or run::

    wget http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz 
    unxz ubuntu-15.04-snappy-amd64-generic.img.xz

*Note the instructions below are specific to Mac OS, but similar utilities exist for Linux*

Run the following command from terminal to verify the path of SD card::

    diskutil list

The output shows all the disks current mounted on the system. Look for the path of your SD card by size and name::

    /dev/disk3
    #:                       TYPE NAME                    SIZE       IDENTIFIER
    0:     FDisk_partition_scheme                        *8.0 GB     disk3
    1:                 DOS_FAT_32 RPISDCARD               8.0 GB     disk3s1


In this example ``dev/disk3`` is the path the SD card. 

Unmount the current partition on the SD card in order to sucessfully use ``dd`` to write::
    
    diskutil unmount /dev/disk3s1

Use ``dd`` command to write image file (Note the ``r`` added to ``rdisk3`` which drastically improves write performance) to the disk. (Note: ``bs`` stands for block size in bytes.)

Go to the directory where your .img located and run command below::

    sudo dd if=ubuntu-15.04-snappy-amd64-generic.img of=/dev/rdisk3 bs=2m

Should take a few minutes to complete.


Connect over serial
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Connect the serial output through USB and start ``minicom``, set baud rate to 9600.

If everything worked properly you should be prompted for a username/password::

    login: ubuntu  
    password: ubuntu

See basic snappy commands `here <https://developer.ubuntu.com/en/snappy/tutorials/using-snappy/>`_.


Flashing RaspberryPi Gen2
-----------------------------

Make sure your Raspberry Pi is the Generation 2 version, otherwise, all Gen1 will not work since Ubuntu Snappy requires ``ARMv7`` architecture.

Flashing image into MicroSD card for RaspberryPi 2 is similar to the instructions above.
Download the corresponding images and following the instructions above should work. 

Detailed instructions can be found `here <https://developer.ubuntu.com/en/snappy/start/#snappy-raspi2>`_.


Flashing BegalBone Black
-----------------------------

Flashing image into MicroSD card for BegalBone Black is similar to the instruction above. 
Download the corresponding images and following the instruction above should work. 

Detail instructions can be found `here <https://developer.ubuntu.com/en/snappy/start/#try-beaglebone>`_.
