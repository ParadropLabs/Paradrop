Chute Configuration
===================

The chute configuration is a YAML file (paradrop.yaml) that a chute
developer creates to configure how resources from the host operating
system should be allocated to the chute. The chute configuration may
also appear in JSON format, particularly when manipulating it through
the Local HTTP API or through the cloud API. This page describes the
structure and interpretation of values in the chute configuration.

Chute Configuration Object
--------------------------

.. jsonschema:: chute-config-schema.json

Chute Network Object
--------------------

Chutes may have one or more network interfaces. All chutes are configured
with a default *eth0* interface that provides WAN connectivity. Chutes
may request additional network interfaces of various types by defining
them in the *net* object. *net* is a dictionary, so each network object
has a name of your choosing. The network name corresponds to the network
name in certain Local API endpoints such as
``/api/v1/chutes/(chute)/networks/(network)``.

WiFi AP Configuration
~~~~~~~~~~~~~~~~~~~~~

A WiFi AP interface is created by setting *type=wifi* and *mode=ap*.
*ap* is the default mode for chute WiFi interfaces, so the latter option
can be omitted.

.. jsonschema:: chute-ap-network-schema.json

Monitor-mode Interface Configuration (Experimental)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A monitor-mode interface enables a chute to observe all detected
WiFi traffic with RadioTap headers.

.. jsonschema:: chute-monitor-interface-schema.json

VLAN Interface Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A VLAN interface allows tagged traffic on the physical Ethernet ports of
the device to be received by the chute. The interface must be configured
with a VLAN ID. Incoming traffic with that VLAN tag will be untagged and
forwarded to the chute interface. Likewise, traffic leaving the chute
interface will be tagged and sent on one the physical ports.

.. jsonschema:: chute-vlan-interface-schema.json

Example
-------

The following example chute configuration sets up a WiFi access point
and a web server running on port 5000. First, we show the example in
YAML format.

.. code-block:: yaml

   net:
     wifi:
       type: wifi
       intfName: wlan0
       dhcp:
         start: 3
         limit: 250
         lease: 1h
       ssid: Free WiFi
       options:
         isolate: true
         maxassoc: 100
   web:
     port: 5000

Here is the same example in JSON format.

.. code-block:: json

   {
     "net": {
       "wifi": {
         "type": "wifi",
         "intfName": "wlan0",
         "dhcp": {
           "start": 3,
           "limit": 250,
           "lease": "1h"
         },
         "ssid": "Free WiFi",
         "options": {
           "isolate": true,
           "maxassoc": 100
         }
       }
     },
     "web": {
       "port": 5000
     }
   }

Experimental Features
---------------------

ParaDrop is under heavy development. Features marked as *experimental*
may be incomplete or buggy. Please contact us if you need help with any
of these features.
