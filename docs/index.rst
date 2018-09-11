.. paradrop documentation master file, created by
   sphinx-quickstart on Sat Jun 20 18:46:21 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 2
   :hidden:

   overview/index
   architecture/index
   device/index
   manual/index
   application/index
   faq
   development/index
   api/index
   pdtools
   paradrop/paradrop


ParaDrop - Enabling Edge Computing at the Extreme Edge
=======================================================

ParaDrop is an open source edge computing platform developed by the `WiNGS Lab <https://wingslab.cs.wisc.edu/>`_
at the University of Wisconsin-Madison.
We built the ParaDrop platform with WiFi routers, so that we can "paradrop" services from the cloud
to the extreme wireless edge - just one hop from user's mobile devices, data sources, and actuators of IoT applications.
The name "ParaDrop" comes from the ability
to "drop" supplies and resources ("services") into the network edge.

.. image:: images/paradrop_overview.png
   :align: center

The above figure gives a high level overview of ParaDrop, including the ParaDrop platform and two example applications.
With the ParaDrop API, third-party applications can deploy services into the network edge - the WiFi routers.
More information about the design and evolution of ParaDrop can be found in the `paper <http://pages.cs.wisc.edu/~suman/courses/707/papers/paradrop-sec2016.pdf>`_.

Getting Started
====================================

Please visit the :doc:`manual/index` page for a quick introduction about how to use ParaDrop.


Where to go from here?
====================================

We have document about ParaDrop application development found under :doc:`application/index`.
If you are interested in working on the development of the ParaDrop platform (our github code) then check out: :doc:`development/index`.
