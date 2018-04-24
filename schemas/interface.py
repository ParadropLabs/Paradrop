"""
Chute Configuration Schema

This module constructs a chute configuration JSON Schema from JSL
specification.
"""

import json

import jsl


class DHCPService(jsl.Document):
    leasetime = jsl.StringField(
        description="Duration of client leases, e.g. 2h.",
        pattern="\d+[dhms]"
    )
    limit = jsl.IntField(
        description="Size of address range beginning at start value.",
        minimum=1
    )
    start = jsl.IntField(
        description="Starting offset for address assignment.",
        minimum=3
    )


class WirelessOptions(jsl.Document):
    ssid = jsl.StringField(
        description="ESSID to broadcast.",
        max_length=32
    )
    key = jsl.StringField(
        description="Wireless network password.",
        min_length=8
    )
    nasid = jsl.StringField(
        description="NAS identifier for RADIUS."
    )
    acct_server = jsl.StringField(
        description="RADIUS accounting server."
    )
    acct_secret = jsl.StringField(
        description="RADIUS accounting secret."
    )
    acct_interval = jsl.IntField(
        description="RADIUS accounting update interval (seconds).",
        minimum=1
    )
    hidden = jsl.BooleanField(
        description="Disable broadcasting the ESSID in beacons."
    )
    isolate = jsl.BooleanField(
        description="Disable forwarding traffic between connected clients."
    )
    maxassoc = jsl.IntField(
        description="Maximum number of associated clients.",
        minimum=0
    )


class InterfaceRequirements(jsl.Document):
    hwmode = jsl.StringField(
        description="Required operating mode (11b for old hardware, 11g for 2.4 GHz, 11a for 5 Ghz).",
        enum=["11b", "11g", "11a"]
    )
    ipv4_network = jsl.StringField(
        description="Required IP network in slash notation.",
        pattern="^\d+\.\d+\.\d+\.\d+/\d+"
    )


class Interface(jsl.Document):
    class Options(object):
        definition_id = "interface"
        title = "Interface Specification"

    type = jsl.StringField(
        description="Network interface type.",
        enum=["monitor", "vlan", "wifi-ap"],
        required=True
    )

    dhcp = jsl.DocumentField(DHCPService)
    dns = jsl.ArrayField(
        description="List of DNS servers to advertise to connected clients.",
        items=jsl.StringField()
    )
    wireless = jsl.DocumentField(WirelessOptions)
    requirements = jsl.DocumentField(InterfaceRequirements)

    l3bridge = jsl.StringField(
        description="Bridge to another network using ARP proxying (experimental)."
    )
    vlan_id = jsl.IntField(
        name="vlan-id",
        description="VLAN tag for traffic to and from the interface.",
        minimum=1,
        maximum=4094
    )
