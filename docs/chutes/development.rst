Chute Development
=============================

Minimally, a chute has a Dockerfile, which contains instructions for
building and preparing the application to run on Paradrop.  A chute
will usually also require scripts, binaries, configuration files, and
other assets.  For integration with the Paradrop toolset, we highly
recommend developing a chute as a `GitHub <https://github.com>`_ project,
but other organization methods are possible.

We will examine the `hello-world
<https://github.com/ParadropLabs/hello-world>`_ chute as an example of
a complete Paradrop application.

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
application to run on Paradrop.  Here is a minimal Dockerfile for our
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

**ADD chute/index.html index.html**

The ADD instruction copies a file or directory from the source repository
to chute filesystem.  This is useful for installing scripts, binaries,
assets, or other files required by the chute.  The <source> path should be
inside the respository, and the <destination> path should be an absolute
path or a path inside the chute's working directory.  Here we install
the index.html file from our source repository to the search directory
used by nginx.

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
*ubuntu:14.04* as the base image gives access to any packages that can
be installed through apt-get.
