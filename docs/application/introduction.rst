Introduction
=============================

ParaDrop is a software platform that enables services to run on Wi-Fi routers.
We call these services *chutes* as in *parachutes*.

ParaDrop runs on top of `Ubuntu Core <https://developer.ubuntu.com/core>`_, a
lightweight, transactionally updated operating system designed for deployments
on embedded and IoT devices, cloud and more.  It runs a new breed of secure,
remotely upgradeable Linux app packages known as snaps.  We support chute
deployment through containerization powered by `Docker
<https://www.docker.com/>`_.

Minimally, a chute has a Dockerfile, which contains instructions for
building and preparing the application to run on ParaDrop.
A chute will usually also require scripts, binaries, configuration files, and
other assets.  For integration with the ParaDrop toolset, we highly
recommend developing a chute as a `GitHub <https://github.com>`_ project,
but other organization methods are possible.

We will examine the `hello-world
<https://github.com/ParadropLabs/hello-world>`_ chute as an example of a
complete ParaDrop application.

Structure
-----------------------

Our hello-world chute is a git project with the following files::

    chute/index.html
    Dockerfile
    README.md
    paradrop.yaml

The top-level contains a README, a Dockerfile, and a special file called
"paradrop.yaml", which will be discussed below.  As a convention,
we place files that will be used by the running application in a
subdirectory called "chute".  This is not necessary but helps keep the
project organized.  Valid alternatives include "src" or "app".

paradrop.yaml
-----------------------

The paradrop.yaml file, which is unique to the ParaDrop platform, contains
important metadata about the project. ParaDrop uses this information
to run the chute on an edge node and also determine what to present to
the user.

Here is an example from the hello-world chute::

    name: hello-world
    description: This project demonstrates a very simple...
    version: 1
    type: normal
    config:
      web:
        port: 80

This example is fairly self-explanatory. It shows a name, description,
and version for the chute, which will be shown on interfaces that present
the running software on the node.

This example is based on an older, more limited syntax, which can only
run one service per chute. For a more complete example and documentation,
refer to :doc:`../api/chute-configuration`.

**type: normal**

This declaration indicates the type of the chute, which tells ParaDrop
how to build and install it. *Normal* chutes build from a Dockerfile, which
we see is present in this project. This is in contrast with *light* chutes
described in :doc:`lightchutes`.

**port: 80**

This declaration indicates that the chute runs a web server on port 80.
ParaDrop will use this information to expose the service externally
to users.

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

The Paradrop daemon exposes some functionality and configuration options to
running chutes through an HTTP API.  This aspect of Paradrop is under rapid
development, and new features will be added with every release.  The host API
is available to chutes through the URL "http://paradrop.io/api/v1".  Paradrop
automatically configures chutes to resolve "paradrop.io" to the ParaDrop device
itself, so these requests go to the ParaDrop daemon running on the router and
not to an outside server.

Authorization
"""""""""""""

In order to access the host API, chutes must pass a token with every request
that proves the authenticity of the request.  When chutes are installed on a
ParaDrop router, they automatically receive a token through an environment
variable named "PARADROP_API_TOKEN".  The chute should read this environment
variable and pass the token as a Bearer token in an HTTP Authorization header.
Here is an example in Python using the `Requests library
<http://docs.python-requests.org/en/master/>`_.::

    import os
    import requests

    CHUTE_NAME = os.environ.get('PARADROP_CHUTE_NAME', 'chute')
    API_TOKEN = os.environ.get('PARADROP_API_TOKEN', 'NA')

    headers = { 'Authorization': 'Bearer ' + API_TOKEN }
    url = 'http://paradrop.io/api/v1/chutes/{}/networks'.format(CHUTE_NAME)
    res = requests.get(url, headers=headers)
    print(res.json())

Please refer to :doc:`../api/index` for a complete listing
of API functions.
