Update Objects
==============

Update objects are used to install and delete chutes as well as change
the router host configuration.  The updateClass and updateType fields
are used to indicate what operation should be performed.

The chute operation called "update" will behave install a chute under
the following conditions:
- No version of the chute is currently installed.
- The new version is greater than the currently installed version.

If a failure is detected while performing an update operation, the system
gracefully rolls back to the previous working state.  This includes restoring
the previously installed version of a chute.

Required Fields
---------------

- updateClass: string, one of ["ROUTER", "CHUTE"]
- updateType: string
  This can one of ["create", "update", "delete", "start", "stop"] for
  chute operations or "sethostconfig" for router operations.
- name: string, either the chute name or `__PARADROP__` for router operations.
  This field must be present for delete, start, and stop operations which only
  need the name of the chute.
- config: config object (see either chute or hostconfig below)
  This must be present for create, update or sethostconfig operations.

Examples
--------

### Install a chute

```json
{
    "updateClass": "CHUTE",
    "updateType": "create",
    "config": {
        "owner": "Paradrop",
        "date": "2015-07-30",
        "name": "hello-world",
        "version": 1,
        "description": "Hello world chute",
        "download": {
            "url": "https://github.com/lhartung/test-chute"
        },
        "environment": {
            "CUSTOM_VARIABLE": 42
        },
        "resources": {
            "cpu_fraction": 0.25
        }
    }
}
```

### Delete a chute

```json
{
    "updateClass": "CHUTE",
    "updateType": "delete",
    "name": "hello-world"
}
```

Chute Configuration Object
==========================

See the Example-Apps repository for examples:
https://github.com/ParadropLabs/Example-Apps

Updates use the same object model as the config.yaml files in the examples
but expect JSON instead of YAML.

Required Fields
---------------

- owner: string (not used)
- date: string in YYYY-mm-dd format (not used)
- name: string, name of the chute
- description: string
- version: int > 0

Optional Fields
---------------

"dockerfile" and "download" are mutually exclusive.  Either embed the
full Dockerfile in the configuration object or use "download" to specify
a URL for the project.  The download method is supported for github
projects and any web URL that points to tar/tar.gz file.

- dataDir: (default: /data) directory inside the chute that will be used
  to store persistent data across chute restarts and upgrades.
- dockerfile: string containing contents of Dockerfile.
- download: object containing "url" field and optionally "user" and
  "secret" fields for authentication.
- environment: dictionary of environment variables to set on
  the running container, these can be used to specify configuration
  options or secrets for the application at install time.
- host_config: object, used to request settings such as port bindings.
- external_image: string, name of Docker image.  If this field is set, the
  router will attempt to pull the image.
- net: object, used to configure the chute's network environment,
  particularly wireless settings.
- systemDir: (default: /paradrop) directory inside the chute that can
  be used to read system information such as a list of devices connected
  to the WiFi access point.
- resources: dictionary of options for reserving compute resources.

Configuring an Access Point
---------------------------

Chutes can add one or more access points to the "net" section of their
configuration.  These sections are named.  In the example below, the
section is named "wifi".

```json
"net": {
    "wifi": {
        "type": "wifi",
        "intfName": "wlan0",
        "ssid": "Paradrop-f214",
        "dhcp": {
          "lease": "12h",
          "start": 100,
          "limit": 100
        },
        "key": "password"
    }
}
```

- type: must be "wifi".
- intfName: is the name of the interface that will appear inside the
chute.
- ssid: is the broadcasted ESSID.  It must be 1-32 characters in length
(inclusive).
- dhcp: specifies parameters for the DHCP service.  If this section is
omitted, the host will not run a DHCP server for this access point.
- key: password for the network.  It must be 8-64 characters in length
(inclusive).

Configuring a Monitor Interface
-------------------------------

Chutes can request a WiFi monitor interface.  Monitor interfaces enable
a chute to record all WiFi activity detected by the device including
beacons and managament frames.  The radiotap header includes additional
information such as signal strength.

While a single WiFi device can host multiple chutes' access points,
a chute requesting a monitor interfaces must be able to obtain exclusive
access to the physical device or the request cannot be fulfilled.
In practice, this limits the number of chutes that can be running
with monitor interfaces to one or two.

```json
"net": {
    "mon": {
        "type": "wifi",
        "intfName": "wlan0",
        "mode": "monitor"
    }
}
```

- type: must be "wifi".
- intfName: is the name of the interface that will appear inside the
chute.
- mode: must be "monitor".

Host Configuration
==================

The host configuration has four sections: "wan", "lan", "wifi", and
"wifi-interfaces".

The "wifi" section sets up physical device settings.  Right now it is
just the channel number.  Other settings related to 11n or 11ac may go
there as we implement them.  These sections should be present even
if there are no objects in "wifi-interfaces".  Removing an interface
from the "wifi" section will make it unavailable to chutes.

The "wifi-interfaces" section sets up virtual interfaces.  Each virtual
interface has an underlying physical device, but there can be multiple
interfaces per device up to a limit set somewhere in the driver,
firmware, or hardware.  Virtual interfaces can be configured as APs as
in the example. They could also be set to client mode and connect to
other APs, but this is not supported currently.

Advanced wifi device settings:
- For 2.4 GHz channels, set hwmode="11g", and for 5 GHz, set hwmode="11a".
It may default to 802.11b (bad, slow) otherwise.
- For a 40 MHz channel width in 802.11n, set htmode="HT40+" or htmode="HT40-".
Plus means add the next higher channel, and minus means add the lower channel.
For example, setting channel=36 and htmode="HT40+" results in using
channels 36 and 40.
- If the hardware supports it, you can enable short guard interval
for slightly higher data rates.  There are separate settings for each
channel width, short_gi_20, short_gi_40, short_gi_80, short_gi_160.
Most 11n hardware can support short_gi_40 at the very least.

Example
-------

```json
{
    "firewall": {
        "defaults": {
            "input": "DROP",
            "output": "ACCEPT",
            "forward": "ACCEPT"
        },
        "rules": [{
            "src": "wan",
            "target": "ACCEPT",
            "proto": "tcp",
            "dest_port": 22
        }]
    },
    "lan": {
        "dhcp": {
            "leasetime": "12h",
            "limit": 100,
            "start": 100
        },
        "interfaces": [
            "eth1",
            "eth2"
        ],
        "ipaddr": "192.168.1.1",
        "netmask": "255.255.255.0",
        "proto": "static",
        "firewall": {
            "defaults": {
                "input": "ACCEPT",
                "output": "ACCEPT",
                "forward": "DROP"
            },
            "forwarding": [{
                "src": "lan",
                "dest": "wan"
            }]
        }
    },
    "wan": {
        "interface": "eth0",
        "proto": "dhcp",
        "firewall": {
            "defaults": {
                "masq": true,
                "conntrack": true,
                "input": "DROP",
                "output": "ACCEPT",
                "forward": "ACCEPT"
            }
        }
    },
    "wifi": [
        {
            "channel": 1,
            "phy": "phy0"
        },
        {
            "channel": 36,
            "phy": "phy1",
            "hwmode": "11a",
            "htmode": "HT40+",
            "short_gi_40": true,
            "tx_stbc": 1,
            "rx_stbc": 1
        }
    ],
    "wifi-interfaces": [
        {
            "device": "phy0",
            "ssid": "paradrop",
            "mode": "ap",
            "network": "lan",
            "ifname": "wlan0"
        },
        {
            "device": "phy1",
            "ssid": "paradrop-5G",
            "mode": "ap",
            "network": "lan",
            "ifname": "wlan1"
        }
    ],
    "system": {
        "onMissingWiFi": "reboot"
    }
}
```

Here are a few ways we can modify the example configuration:
- If we want to run a second AP on the second device, we can add a
  section to wifi-interfaces with device="wlan1" and ifname="wlan1".
- If we want to run a second AP on the first device, we can add a
  section to wifi-interfaces with device="wlan0" and an ifname that is
  different from all others interfaces sharing the device.
  We should avoid anything that starts with "wlan" except the case
  where the name exactly matches the device.
  For device "wlan0", acceptable names would be "wlan0", "pd-wlan", etc.
  Avoid "vwlan0.X" and the like because that would conflict with chute interfaces,
  but "hwlan0.X" would be fine.
- If we want to add WPA2, set encryption="psk2" and key="the passphrase"
  in the wifi-interface section for the AP.
  Based on standard, the Passphrase of WPA2 must be between 8 and 63 characters, inclusive.
