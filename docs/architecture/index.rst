System Architecture
====================================

This section details some of the non-obvious architectural features of ParaDrop.

ParaDrop has three major components: the ParaDrop router, the ParaDrop controller, and the ParaDrop API.

ParaDrop router
--------------------
The ParaDrop router is the key part of the ParaDrop platform.
In addition to a normal WiFi access point, it provides the substrate to deploy edge computing services on.
We have built the reference ParaDrop routers based on PC Engines APU and APU2 single board computer.
The image below shows a router built with a PC Engines APU board.

.. image:: ../images/paradrop_router.png
   :align: center

The ParaDrop software implementation does support various hardware platform.
We can also try the functions of ParaDrop with virtual machines.
Please visit the :doc:`../device/index` page for more information about hardware setup for ParaDrop routers.

ParaDrop controller
----------------------
The ParaDrop controller is deployed in `paradrop.org <https://paradrop.org>`_.
Users can sign up and create an account through the web page.
For end users, it provides a dashboard to configure and monitor the ParaDrop routers they have permissions.
They can also manage the edge computing services (we call them chutes, in short of parachutes) running on the ParaDrop routers.
For developers, it provides the interface that developers can register their applications and manage the chutes.

ParaDrop API
----------------
ParaDrop exports the platform's capability through an API.
Based on the functionality and position, the API can be divided into two parts: the cloud part and the edge part.
The cloud part provides the management interfaces for applications to orchestrate the chutes from the cloud.
Examples include resource permission management, chute deployment and management, router configuration management, etc..
The edge part exports the local context information of the routers to the chutes to do some useful things locally.
Examples include local wireless channel information, local wireless peripheral device access, etc..
