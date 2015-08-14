Installing Paradrop on hardware
====================================

Paradrop is distributed as a "snap" or an application that runs on Snappy Ubuntu.
You can run snappy on any x86 or armv7 board (Raspberry Pi Gen 2 or Beagleboard Black supported!) 

To setup Paradrop you need to install snappy on your hardware of choice and then have snappy install paradrop.
This is a temporary method until more robust installation tools are finished. 

First flash the board with the snappy image, see :doc:`flashing`.

Next install docker::

    ssh into the router
    sudo snappy install docker


*From your development machine* (because you cannot install unauthorized snaps internally, only using ``snappy-remote`` for now).


Next install a few required programs not in the Snappy package system yet::
    
    wget https://paradrop.io/storage/snaps/dnsmasq_2.74_all.snap
    snappy-remote --url=ssh://<ip>:8022 install dnsmasq*.snap

    wget https://paradrop.io/storage/snaps/hostapd_2.4_all.snap
    snappy-remote --url=ssh://<ip>:8022 install hostapd*.snap


Finally, install Paradrop, unfortunately this is not an officially supported Snappy package yet so it must be installed manually using snappy tools::

    #From the Paradrop github repo:
    cd paradrop
    python setup.py bdist_egg -d ../buildenv
    cd ..
    [ ! -f snap/bin/pipework ] && wget https://raw.githubusercontent.com/jpetazzo/pipework/3bccb3adefe81b6acd97c50cfc6cda11420be109/pipework -O snap/bin/pipework
    chmod 755 snap/bin/pipework

    rm -f snap/bin/pd

    pex --disable-cache paradrop -o snap/bin/pd -m paradrop:main -f buildenv/
    rm -rf *.egg-info

    snappy build snap
    snappy-remote --url=ssh://localhost:8022 install <snap-location>
