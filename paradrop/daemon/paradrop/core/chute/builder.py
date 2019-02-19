"""
The Chute Builder interprets the chute specification, which comes from a
paradrop.yaml file or from a JSON object via a cloud update. The Chute
Builder then produces a valid Chute ojbect with one or more Service
objects.

There are different versions of the chute specification in code
repositories, and so the intent is to encapsulate this complexity within
the ChuteBuilder implementation. Other code modules, especially the
execution plan pipeline, should be able to rely on a relatively stable
Chute and Service object interface.

+----------------------------+                   +---------------+
|                            |         interpret |               |
| Chute Specification        | <-----------------+ Chute Builder |
| serialized as YAML or JSON |                   |               |
| in a variety of formats    |                   ++-------------++
|                            |                    |             |
+----------------------------+                    |  construct  |
                                                  |             |
                                                  v             |
                                                                |
+----------------+                         +-------+            |
|                |                         |       |            |
| Execution Plan |                         | Chute |            v
| -------------- +-----------------------> |       | has 1+
| function 1     |                         +-------o---+---------+
| ...            | consume                             |         |
| function N     |                                     | Service |
|                +-----------------------------------> |         |
+----------------+                                     +---------+
"""
import six

from .chute import Chute
from .service import Service


WIRELESS_OPTIONS = set([
    "ssid",
    "key",
    "nasid",
    "acct_server",
    "acct_secret",
    "acct_interval",
    "hidden",
    "isolate",
    "maxassoc"
])


def fix_interface_type(interface):
    orig_type = interface.get("type")
    orig_mode = interface.get("mode", "ap")

    if orig_type == "wifi":
        return "wifi-{}".format(orig_mode)
    else:
        return orig_type


def fix_wireless_options(interface):
    wireless = interface.get("wireless", {})

    for key, value in six.iteritems(interface):
        if key in WIRELESS_OPTIONS:
            wireless[key] = value

    for key, value in six.iteritems(interface.get("options", {})):
        if key in WIRELESS_OPTIONS:
            wireless[key] = value

    return wireless


class ChuteBuilder(object):
    """
    Build a composite chute object from a chute specification.

    Implementations of ChuteBuilder are responsible for interpreting
    the chute specification, which comes from a paradrop.yaml file or
    JSON object via cloud update. The ChuteBuilder then produces a valid
    Chute object with one or more Service objects.
    """
    def configure_chute(self, spec):
        for field in ["name", "version", "description"]:
            value = spec.get(field, "unknown")
            setattr(self.chute, field, value)

    def create_chute(self, spec):
        return NotImplemented

    def create_services(self, spec):
        return NotImplemented

    def get_chute(self):
        return self.chute


class SingleServiceChuteBuilder(ChuteBuilder):
    """
    Build a pre-0.12 single-service chute.

    ** Example configuration**:

    .. sourcecode:: yaml

       name: seccam
       description: A Paradrop chute that performs motion detection using a simple WiFi camera.
       version: 1

       net:
         wifi:
           type: wifi
           intfName: wlan0
           dhcp:
             start: 4
             limit: 250
             lease: 12h
           ssid: seccam42
           key: paradropseccam
           options:
             isolate: true
             maxassoc: 100
       web:
         port: 5000
    """

    # Fields that should be present in updates but not chute objects.
    UpdateSpecificArgs = ['deferred']

    def create_chute(self, spec):
        self.chute = Chute()
        self.chute.name = spec.get("name")
        self.chute.description = spec.get("description", None)
        self.chute.environment = spec.get("environment", {})
        self.chute.owner = spec.get("owner", None)
        self.chute.version = spec.get("version", None)

        config = spec.get("config", {})
        self.chute.config = config
        self.chute.web = config.get("web", {})

        # Old chutes did not specify the web service because it was implied.
        if "port" in self.chute.web:
            self.chute.web['service'] = "main"

    def create_services(self, spec):
        service = Service(chute=self.chute, name="main")

        service.command = spec.get("command", None)
        service.image = spec.get("use", None)
        service.source = "."
        service.type = spec.get("type", "normal")

        config = spec.get("config", {})

        # Covert old-style structure with arbitrary names to new-style that is
        # indexed by interface name.
        interfaces = {}
        for iface in config.get("net", {}).values():
            iface['type'] = fix_interface_type(iface)

            if iface['type'].startswith("wifi"):
                iface['wireless'] = fix_wireless_options(iface)

            interfaces[iface['intfName']] = iface

        requests = {}
        requests['as-root'] = spec.get("as_root", False)

        try:
            requests['port-bindings'] = config['host_config']['port_bindings']
        except KeyError:
            requests['port-bindings'] = {}

        # Find extra build options, particularly for light chutes.
        build = {}
        for key in ["image_source", "image_version", "packages"]:
            if key in config:
                build[key] = config[key]

        service.build = build
        service.environment = config.get("environment", {})
        service.interfaces = interfaces
        service.requests = requests

        self.chute.add_service(service)


class MultiServiceChuteBuilder(ChuteBuilder):
    """
    Build a modern multi-service chute.

    ** Example configuration**:

    .. sourcecode:: yaml

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
    """
    def create_chute(self, spec):
        self.chute = Chute({})

        for field in ["name", "version", "description", "owner"]:
            value = spec.get(field, "unknown")
            setattr(self.chute, field, value)

        self.chute.environment = spec.get("environment", {})
        self.chute.web = spec.get("web", {})

    def create_services(self, spec):
        for name, spec in six.iteritems(spec.get("services", {})):
            service = Service(chute=self.chute, name=name)

            service.command = spec.get("command", None)
            service.image = spec.get("image", None)
            service.source = spec.get("source", ".")
            service.type = spec.get("type", "normal")

            service.build = spec.get("build", {})
            service.environment = spec.get("environment", {})
            service.interfaces = spec.get("interfaces", {})
            service.requests = spec.get("requests", {})

            # Make sure the intfName field exists for code that depends on it.
            for name, iface in six.iteritems(service.interfaces):
                iface['intfName'] = name

            self.chute.add_service(service)


def build_chute(spec):
    if 'services' in spec:
        builder = MultiServiceChuteBuilder()
    else:
        builder = SingleServiceChuteBuilder()

    builder.create_chute(spec)
    builder.create_services(spec)

    return builder.get_chute()


def rebuild_chute(spec, updates):
    for field in ["name", "version", "description", "owner", "environment", "web"]:
        if field in updates:
            spec[field] = updates[field]

    return build_chute(spec)
