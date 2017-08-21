Introduction
=============================

ParaDrop is a software platform that enables services/apps to run on Wi-Fi routers.
We call these apps "chutes" like a parachute.

ParaDrop runs on top of `Ubuntu Core <https://developer.ubuntu.com/core>`_,
a lightweight, transactionally updated operating system designed for deployments on embedded and IoT devices, cloud and more.
It runs a new breed of super-secure, remotely upgradeable Linux app packages known as snaps.
We also enable our apps through containerization by leveraging `Docker <https://www.docker.com/>`_.

Minimally, a chute has a Dockerfile, which contains instructions for
building and preparing the application to run on ParaDrop.
A chute will usually also require scripts, binaries, configuration files, and
other assets.  For integration with the ParaDrop toolset, we highly
recommend developing a chute as a `GitHub <https://github.com>`_ project,
but other organization methods are possible.

We will examine the `hello-world <https://github.com/ParadropLabs/hello-world>`_
chute as an example of a complete ParaDrop application.

Structure
-----------------------

Our hello-world chute is a git project with the following files::

    chute/index.html
    Dockerfile
    README.md

The top-level contains a README and a special file called "Dockerfile",
which will be discussed below.  As a convention, we place files that
will be used by the running application in a subdirectory called "chute".
This is not necessary but helps keep the project organized.  Valid
alternatives include "src" or "app".

Dockerfile
-----------------------

The Dockerfile contains instructions for building and preparing an
application to run on ParaDrop.  Here is a minimal Dockerfile for our
hello-world chute::

    FROM nginx
    ADD chute/index.html /usr/share/nginx/html/index.html

**FROM nginx**

The FROM instruction specifies a base image for the chute.  This could
be a Linux distribution such as "ubuntu:14.04" or an standalone
application such as "nginx".  The image name must match an image in
the Docker public registry.  We recommend choosing from the `official
repositories <https://hub.docker.com/explore/>`_.  Here we use "nginx"
for a light-weight web server.

**ADD <source> <destination>**

The ADD instruction copies a file or directory from the source repository
to the chute filesystem.  This is useful for installing scripts or
other files required by the chute and are part of the source repository.
The <source> path should be inside the respository, and the <destination>
path should be an absolute path or a path inside the chute's working
directory.  Here we install the index.html file from our source repository
to the search directory used by nginx.

Other useful commands for building chutes are RUN and CMD.  For a
complete reference, please visit the official `Dockerfile reference
<https://docs.docker.com/engine/reference/builder/>`_.

Here is an alternative implementation of the hello-world Dockerfile that
demonstrates some of the other useful instructions. ::

    FROM ubuntu:14.04
    RUN apt-get update && apt-get install -y nginx
    ADD chute/index.html /usr/share/nginx/html/index.html
    EXPOSE 80
    CMD ["nginx", "-g", "daemon off;"]

Here we use a RUN instruction to install nginx and a CMD instruction
to set nginx as the command to run inside the chute container.  Using
"ubuntu:14.04" as the base image gives access to any packages that can
be installed through apt-get.

Persistent Data
-----------------------

Each running chute has a persistent data storage that is not visible
to other chutes.  By default the persistent data directory is named
"/data" inside the chute's filesystem.  Files stored in this directory
will remain when upgrading or downgrading the chute and are only removed
when uninstalling the chute.

System Information
-----------------------

The ParaDrop daemon share system information with chutes through
a read-only directory named "/paradrop".  Chutes that are configured
with a WiFi access point will find a file in this directory that lists
wireless clients.  In future versions there will also be information
about Bluetooth and other wireless devices.

dnsmasq-wifi.leases
"""""""""""""""""""

This file lists client devices that have connected to the chute's WiFi network
and received a DHCP lease.  This is a plain text file with one line
for each device containing the following space-separated fields.

1. DHCP lease expiration time (seconds since Unix epoch).
2. MAC address.
3. IP address.
4. Host name, if known.
5. Client ID, if known; the format of this field varies between devices.

The following example shows two devices connected to the chute's WiFi
network. ::

    1480650200 00:11:22:33:44:55 192.168.128.130 android-ffeeddccbbaa9988 *
    1480640500 00:22:44:66:88:aa 192.168.128.170 someones-iPod 01:00:22:44:66:88:aa


Chute-to-Host API
-----------------

The Paradrop daemon exposes some functionality and configuration
options to running chutes through an HTTP API.  This aspect of Paradrop
is under rapid development, and new features will be added with
every release.  The host API is available to chutes through the URL
"http://home.paradrop.org/api/v1".  Paradrop automatically configure
chutes to resolve "home.paradrop.org" to the ParaDrop device itself,
so these requests go to the ParaDrop daemon running on the router and
not to an outside server.

Authorization
"""""""""""""

In order to access the host API, chutes must pass a token with every request
that proves the authenticity of the request.  When chutes are installed on a
ParaDrop router, they automatically receive a token through an environment variable
named "PARADROP_API_TOKEN".  The chute should read this environment variable
and pass the token as a Bearer token in an HTTP Authorization header.
Here is an example in Python using the `Requests library
<http://docs.python-requests.org/en/master/>`_.::

    import os
    import requests

    CHUTE_NAME = os.environ.get('PARADROP_CHUTE_NAME', 'chute')
    API_TOKEN = os.environ.get('PARADROP_API_TOKEN', 'NA')

    headers = { 'Authorization': 'Bearer ' + API_TOKEN }
    url = 'http://home.paradrop.org/api/v1/chutes/{}/networks'.format(CHUTE_NAME)
    res = requests.get(url, headers=headers)
    print(res.json())

/chutes/<chute name>/networks
"""""""""""""""""""""""""""""

* Purpose: List networks (such as Wi-Fi networks) configured for the chute.
* Methods: GET
* Returns: [ object ]

Note: there are currently not many different types of networks supported
for chutes, so most chutes will either have no networks (empty list) or
a list containing a single entry that looks like this.::

    { 'interface': 'wlan0', 'name': 'wifi', 'type': 'wifi' }

/chutes/<chute name>/networks/<network name>/stations
"""""""""""""""""""""""""""""""""""""""""""""""""""""

* Purpose: List devices ("stations") connected to a wireless network.
* Methods: GET
* Returns: [ object ]

For chutes that have configured a Wi-Fi AP, this endpoint provides
detailed information about devices that are connected to the AP, including
MAC address, bytes sent and received, and average signal strength.
Here is an example response.::

    [{'authenticated': 'yes',
      'authorized': 'yes',
      'inactive_time': '36108 ms',
      'mac_addr': '5c:59:48:7d:b9:e6',
      'mfp': 'no',
      'preamble': 'short',
      'rx_bitrate': '65.0 MBit/s MCS 7',
      'rx_bytes': '10211',
      'rx_packets': '168',
      'signal': '-42 dBm',
      'signal_avg': '-43 dBm',
      'tdls_peer': 'no',
      'tx_bitrate': '1.0 MBit/s',
      'tx_bytes': '34779',
      'tx_failed': '0',
      'tx_packets': '71',
      'tx_retries': '0',
      'wmm_wme': 'yes'}]

/chutes/<chute name>/networks/<network name>/stations/<mac address>
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

* Purpose: View or remove a device ("station") connected to a wireless network.
* Methods: GET, DELETE
* Returns: object

GET returns similar information as the request above but for a single
station.  DELETE will kick the device from the wireless network, but
in many cases the device will be able to reconnect.
