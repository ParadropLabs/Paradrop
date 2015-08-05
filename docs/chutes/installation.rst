Installing Paradrop
====================================

Paradrop is distributed as a "snap," or an application that runs on snappy. You can run snappy on any x86 or armv7 board (Raspberry Pi Gen 2 or Beagleboard Black supported!) 

To setup paradrop you need to install snapy on your hardware of choice and then have snappy install paradrop. This is a temporary method until more robust installation tools are finished. 



Flashing x86 Paradrop Boards
++++++++++++++++++++++++++++

These instructions apply to x86 routers distributed by the Paradrop development team. 

Download snappy here: `Ubuntu Snappy <http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz>`_

or run::

    wget http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz 
    unxz ubuntu-15.04-snappy-amd64-generic.img.xz


Run the following command from terminal to verify the path of SD card::

    diskutil list

The output shows all the disks current mounted on the system. Look for the path of your SD card by size and name::

    /dev/disk3
    #:                       TYPE NAME                    SIZE       IDENTIFIER
    0:     FDisk_partition_scheme                        *8.0 GB     disk3
    1:                 DOS_FAT_32 RPISDCARD               8.0 GB     disk3s1


In this example ``dev/disk3`` is the path the SD card. 

Unmount the current partition on the SD card in order to sucessfully use @dd@ to write::
    
    diskutil unmount /dev/disk3s1

Use ``dd`` command to write image file (Note the ``r`` added to ``rdisk3`` which drastically improves write performance) to the disk. (Note: ``bs`` stands for block size in bytes.)


Go to the directory where your .img located and run command below::

    sudo dd if=ubuntu-15.04-snappy-amd64-generic.img of=/dev/rdisk3 bs=2m

Different SD card take different time to finish the process. use @CTRL+T@ to see the current status of @dd@.


First boot: SSH through serial
----------------------------------------

Connect the serial output through USB and start Putty section with @baud rate of 9600@. Plug in SD card into the router and plug in power. The Ubuntu Snappy should automatically boots and runs. 

*Note:* baud rate of 115200 *will not* boot you into the system, *9600* works perfect.  

Once you access the device, Log into the Ubuntu Snappy with login/password below::

    login: ubuntu  
    password: ubuntu

`See here <https://developer.ubuntu.com/en/snappy/tutorials/using-snappy/>`_ for some basic snappy commands.

Lets test the wireless card's functionality. To bring wirelss ``wlan0`` up::

    sudo ifconfig wlan0 up

Search SSIDs nearby with ``scan``::

    sudo iw dev wlan0 scan

If everything works fine, you should expect to see list of different SSIDs around your router. 


On RaspberryPi Generation 2
++++++++++++++++++++++++++++


Make sure your Raspberry Pi is the Generation 2 version, otherwise, all Gen1 will not work since Ubuntu Snappy requires ``ARMv7`` architecture.

Flashing image into MicroSD card for RaspberryPi 2 is similar to the instruction above. 
Download the corresponding images and following the instruction above should work. 

Detail instructions can be found `here <https://developer.ubuntu.com/en/snappy/start/#snappy-raspi2>`_


h2. On BegalBone Black
++++++++++++++++++++++++++++

Flashing image into MicroSD card for BegalBone Black is similar to the instruction above. 
Download the corresponding images and following the instruction above should work. 

Detail instructions can be found `here <https://developer.ubuntu.com/en/snappy/start/#try-beaglebone>`_
