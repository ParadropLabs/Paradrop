Host Configuration
==================

The host configuration is a YAML file that resides on the ParaDrop device and
controls many aspects of system functioning, particularly network and wireless
device configuration. The host configuration may also appear in JSON format
when manipulating it through the Local HTTP API or through the cloud
controller. This page describes the structure and interpretation of values
in the host configuration.

Host Configuration Object
-------------------------

.. jsonschema:: host-config-schema.json

DHCP Object
-----------

.. jsonschema:: host-config-dhcp-schema.json

Firewall Defaults Object
------------------------

.. jsonschema:: host-config-firewall-defaults-schema.json

Wi-Fi Device Object
-------------------

Objects in the *wifi* array define physical device settings such as the
channel and transmit power. These settings affect all interfaces in the
"wifi-interfaces" array that use the corresponding device.

ParaDrop uses a deterministic system for identifying Wi-Fi devices,
so that settings are applied to the same device on startup as long
as there have been no hardware changes. ParaDrop numbers PCI and USB
devices separately starting from zero, so a ParaDrop host with two PCI
Wi-Fi cards and one USB card will have device IDs *pci-wifi-0*,
*pci-wifi-1*, and *usb-wifi-0*.

The spectrum band is determined by the *hwmode* setting and the *channel*
setting. They must be compatible. For 2.4 GHz channels (1-13), set
*hwmode* to *11g*. For 5 GHz channels (36-165), set *hwmode* to *11a*.

Higher data rates and channel sizes (802.11n and 802.11ac) are configured
with the *htmode* setting. For a 40 MHz channel width in 802.11n,
set *htmode=HT40* or *htmode=HT40-*. Plus means add the next higher
channel, and minus means add the lower channel. For example, setting
*channel=36* and *htmode=HT40+* results in using channels 36 and 40 as
a 40 MHz channel.

If the hardware supports it, you can enable short guard interval for
slightly higher data rates. There are separate settings for each channel
width: *short_gi_20*, *short_gi_40*, and *short_gi_80*.

.. jsonschema:: host-config-wifi-device-schema.json

Wi-Fi Interface Object
----------------------

Objects in the *wifi-interfaces* array configure virtual interfaces.
Each virtual interface has an underlying physical device, but there
can be multiple interfaces per device up to a limit determined by
the hardware. Virtual interfaces can be configured as APs or in other
operating modes (with limited support).

The *encryption* setting can take a number of different values.  The most
common options are: "none" for an open access point, "psk2" for WPA2
Personal (PSK), and "wpa2" for WPA2 Enterprise.  WPA2 Enterprise requires
additional configuration to interact with an external RADIUS server.

.. jsonschema:: host-config-wifi-interface-schema.json
