.. paradrop documentation master file, created by
   sphinx-quickstart on Sat Jun 20 18:46:21 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 2
   :hidden:

   chutes/chutedev
   pd/paradropdev
   arch/architecture
   api/modules



Paradrop
====================================

Paradrop is a software platform that enables apps to run on Wi-Fi routers.
We call these apps "chutes" like a parachute.
The name Paradrop comes from the fact that we are enabling the ability to "drop" supplies and resources ("apps") into a difficult and not well-travelled environment - the home.

Our early versions of Paradrop relied on OpenWrt, however we are revamping the platform and tailoring it towards a broader developer community.
Paradrop now runs on top of `Ubuntu Snappy <https://developer.ubuntu.com/en/snappy/>`_, a trimmed-down and secured operating system that can run on ARM and x86.
We also enable our apps through containerization by leveraging `Docker <https://www.docker.com/>`_.


The Paradrop workflow
====================================

There are two components to the Paradrop platform:

* The `build tools <https://pypi.python.org/pypi/pdtools>`_ - our CLI that enables registration, login, and control.
* The `instance tools <https://github.com/ParadropLabs/Paradrop>`_ - our configuration daemons and tools to launch apps on hardware.

.. image:: images/dev_tools_map.png
   :align:  center

As you can see from the image above, we will refer to *Build Tools* when we talk about the CLI program running on your development computer that controls and communicates with the rest of the Paradrop platform.
Treat this tool as your window into the rest of the Paradrop world.
Our *Instance Tools* leverage programs like Docker to allow Paradrop apps to run on router hardware, this could be a Raspberry Pi, or even a virtual machine on your computer that acts as a router.
Using Paradrop, you can actually plug in a USB Wi-Fi adapter and turn a virtual machine on your computer into a real router with our platform!


Getting Started
====================================

This will quickly take you through the process of bringing up a Hello World chute in a virtual machine on your computer.

As of Release 0.1 you must compile using Ubuntu??XXX

1. Install our `build tools <https://pypi.python.org/pypi/pdtools>`_ (``pip install pdtools``).
2. Clone our `instance tools <https://github.com/ParadropLabs/Paradrop>`_.
3. Register an account ``paradrop register``
4. Setup instance tools ``pdbuild.sh setup``
5. Boot local testing VM ``pdbuild.sh up``
6. Build the tools to go into testing VM ``pdbuild.sh build`` (have to be in Ubuntu rightXXX?)
7. Push tools into VM ``pdbuild.sh install``



View Get started writing chutes with :doc:`chutes/chutedev`. 
Learn how to help develop paradrop at :doc:`pd/paradropdev`. 





