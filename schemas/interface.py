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
    wireless = jsl.DocumentField(WirelessOptions)
    requirements = jsl.DictField()
