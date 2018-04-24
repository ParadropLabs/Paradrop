"""
Chute Configuration Schema

This module constructs a chute configuration JSON Schema from JSL
specification.
"""

import json

import jsl

from .service import Service


class ChuteSource(jsl.Document):
    type = jsl.StringField(
        required=True,
        description="Type of source."
    )
    url = jsl.UriField(
        description="URL for accessing source."
    )


class ChuteWebService(jsl.Document):
    service = jsl.StringField(
        description="Name of chute service which provides the web service.",
    )
    port = jsl.IntField(
        description="Listening port inside the chute.",
        minimum=1,
        maximum=65536
    )


class Chute(jsl.Document):
    class Options(object):
        inheritance_mode = jsl.ALL_OF
        title = "Chute Specification"

    name = jsl.StringField(
        required=True,
        description="Name of the chute."
    )
    description = jsl.StringField(
        description="Description of the chute to be shown to users."
    )
    version = jsl.AnyOfField(
        [jsl.StringField(), jsl.NumberField()],
        description="Version of the chute."
    )

    services = jsl.DictField(
        pattern_properties={"\w+": jsl.DocumentField(
            Service,
            as_ref=True,
            title="ChuteService"
        )},
        description="Services to be installed with the chute."
    )

    web = jsl.DocumentField(ChuteWebService)


if __name__ == "__main__":
    schema = Chute.get_schema(ordered=True)

    for name in schema['definitions'].keys():
        schema['definitions'][name]['$$target'] = "#/definitions/{}".format(name)

    out = json.dumps(schema, indent=4)
    print(out)
