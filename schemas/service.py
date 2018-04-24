"""
Chute Configuration Schema

This module constructs a chute configuration JSON Schema from JSL
specification.
"""

import json

import jsl

from .interface import Interface


class PortBinding(jsl.Document):
    external = jsl.IntField(
        description="External (host) port number.",
        minimum=1,
        maximum=65536
    )
    internal = jsl.IntField(
        description="Internal (container) port number.",
        minimum=1,
        maximum=65536
    )


class ChuteRequests(jsl.Document):
    as_root = jsl.BooleanField(
        name="as-root",
        description="Run service as privileged user."
    )
    port_bindings = jsl.ArrayField(
        name="port-bindings",
        description="Port bindings from host to service container.",
        items=jsl.DocumentField(PortBinding)
    )


class Service(jsl.Document):
    class Options(object):
        definition_id = "service"
        title = "Service Specification"

    type = jsl.StringField(
        description="Type of chute service.",
        enum=["light", "normal", "image"]
    )
    source = jsl.StringField(
        description="Source directory for this service."
    )
    image = jsl.StringField(
        description="Image specification for services that pull a Docker image.",
    )
    command = jsl.AnyOfField(
        [jsl.StringField(), jsl.ArrayField(items=jsl.StringField())]
    )

    dns = jsl.ArrayField(
        description="List of DNS servers to be used within the container.",
        items=jsl.StringField()
    )
    environment = jsl.DictField(
        description="Environment variables."
    )
    interfaces = jsl.DictField(
        pattern_properties={"\w{1,16}": jsl.DocumentField(
            Interface,
            as_ref=True,
            title="ChuteInterface"
        )},
        description="Network interfaces to be connected."
    )
    requests = jsl.DocumentField(
        ChuteRequests,
        description="Extra features and privileges requested for the service."
    )
