System Architecture
====================================

This section describes some of the important architectural features of
ParaDrop.  Our discussion will cover three major aspects of the ParaDrop
design.

- The ParaDrop router
- The ParaDrop cloud controller
- The ParaDrop API

ParaDrop router
--------------------

The ParaDrop router is the key part of the ParaDrop platform.  In addition to
being a WiFi access point, it provides the substrate on which edge computing
services can be deployed.  We have built the reference ParaDrop routers based
on the `PC Engines APU <https://pcengines.ch/apu.htm>`_ and APU2 single board
computer.  The image below shows a router built with a PC Engines APU board.

.. image:: ../images/paradrop_router.png
   :align: center

In addition to the PC Engines APU2, the ParaDrop software implementation can be
run on various other hardware platforms as well as virtual machines.  Please
refer to :doc:`../device/index` for more information about hardware setup for
ParaDrop routers.

ParaDrop cloud controller
-------------------------

The ParaDrop cloud controller is hosted at `paradrop.org
<https://paradrop.org>`_ and provides a central location for tracking and
managing ParaDrop routers as well as a Chute Store for software distribution.
Users can sign up for a free account.  For end users and administrators, it
provides a dashboard to configure and monitor the ParaDrop routers under their
control.  The dashboard enables users to manage the services (called *chutes*)
running on their routers.  For developers, it provides the interface through
which applications can be registered as ParaDrop chutes available for
installation on routers.

ParaDrop API
----------------

ParaDrop exports the platform's full capability through an API.  Based on the
functionality and location, the API can be divided into two parts: the cloud
API and the edge API.  The cloud API provides the management interfaces for
applications to orchestrate the chutes from the cloud.  Examples include
resource permission management, chute deployment and management, and router
configuration management.  The edge API exports the local context information
of the routers to the chutes to do some useful things locally.  Examples
include local wireless channel information and local wireless peripheral device
access.
