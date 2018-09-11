Chute Configuration
===================

The chute configuration is a YAML file (paradrop.yaml) that a chute
developer creates to configure how resources from the host operating
system should be allocated to the chute. The chute configuration may
also appear in JSON format, particularly when manipulating it through
the Local HTTP API or through the cloud API. This page describes the
structure and interpretation of values in the chute configuration.

.. jsonschema:: chute.json

Chute Service Object
--------------------

Chutes consist of one or more *services*, which are long-running processes
that implement the functionality of the chute. Services may be built
from code in the chute project, from a Dockerfile, or pulled as images
from the public Docker Hub.

.. jsonschema:: chute.json#/definitions/service

Chute Interface Object
----------------------

Chutes may have one or more network interfaces. All chutes are configured
with a default *eth0* interface that provides WAN connectivity. Chutes
may request additional network interfaces of various types by defining
them in the *interfaces* object. *interfaces* is a dictionary, where the
key should be the desired interface name inside your chute, e.g. *wlan0*.
The same key is used to reference the interface in certain API endpoints
such as
``/api/v1/chutes/(chute)/networks/(network)``.

.. jsonschema:: chute.json#/definitions/interface

WiFi AP Configuration
~~~~~~~~~~~~~~~~~~~~~

A WiFi AP interface is created by setting *type=wifi-ap*.  There are
many options for configuring the WiFi AP available through the wireless
section of the interface object.

Monitor-mode Interface Configuration (Experimental)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A monitor-mode interface enables a chute to observe all detected WiFi
traffic with RadioTap headers. A monitor-mode interface is created by
setting *type=wifi-monitor*.

Monitor-mode interfaces are disallowed by default but can be enabled if
you have administrative access to a node. This is because monitor-mode
interfaces are potentially dangerous. They enable malicious chutes
to record network traffic, and furthermore, the feature itself
is experimental.  There may be issues with kernel drivers or our
implementation that cause system instability.

If you understand the risks and wish to enable monitor-mode interfaces,
connect to your node using SSH and run the following command.::

    snap set paradrop-daemon base.allow-monitor-mode=true

VLAN Interface Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A VLAN interface allows tagged traffic on the physical Ethernet ports of
the device to be received by the chute. The interface must be configured
with a VLAN ID. Incoming traffic with that VLAN tag will be untagged and
forwarded to the chute interface. Likewise, traffic leaving the chute
interface will be tagged and sent on one the physical ports.

Example
-------

The following example chute configuration sets up a WiFi access point
and a web server running on port 5000. It also shows how to install
and connect a database from a public image.

.. code-block:: yaml

  name: seccam
  description: A Paradrop chute that performs motion detection using a simple WiFi camera.
  version: 1

  services:
    main:
      type: light
      source: .
      image: python2
      command: python -u seccam.py

      environment:
        IMAGE_INTERVAL: 2.0
        MOTION_THRESHOLD: 40.0
        SECCAM_MODE: detect

      interfaces:
        wlan0:
          type: wifi-ap

          dhcp:
            leasetime: 12h
            limit: 250
            start: 4

          wireless:
            ssid: seccam42
            key: paradropseccam
            hidden: false
            isolate: true

          requirements:
            hwmode: 11g

      requests:
        as-root: true
        port-bindings:
          - external: 81
            internal: 81

    db:
      type: image
      image: mongo:3.0

  web:
    service: main
    port: 5000

Experimental Features
---------------------

ParaDrop is under heavy development. Features marked as *experimental*
may be incomplete or buggy. Please contact us if you need help with any
of these features.
