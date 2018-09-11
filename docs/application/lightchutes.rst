Developing Light Chutes
=============================

Light chutes build and install the same way as normal chutes and can
do many of the same things.  However, they make use of prebuilt base
images that are optimized for different programming languages. We offer
light chutes as a convenience for projects that only rely on one of the
supported languages and do not need to install other system packages.

Light chutes offer a few advantages over normal chutes.

* **Safety:** Light chutes have stronger confinement properties, so
  you can feel safer installing a light chute written by a third party
  developer.
* **Fast installation:** Light chutes use a common base image that
  may already be cached on the router, so installation can be very
  fast.
* **Simplicity:** You do not need to learn how to write
  and debug a Dockerfile to develop a chute.  Instead, you can
  use the package management tools you may already be using
  (e.g. package.json for npm and requirements.txt for pip).
* **Portability:** With ARM suppport coming soon for ParaDrop,
  your light chutes will most likely run on ARM with extra work on your
  part.  This is not the case for normal chutes that use a custom
  Dockerfile.

We will look at the `node-hello-world
<https://github.com/ParadropLabs/node-hello-world>`_ chute as an example of a
light chute for ParaDrop.

Structure
-----------------------

Our hello-world chute is a git project with the following files::

    README.md
    index.js
    package.json
    paradrop.yaml


The project contains the typical files for a node.js project as well
as a special file called "paradrop.yaml".

paradrop.yaml
-----------------------

The paradrop.yaml file contains information that ParaDrop needs
in order to run the chute.  Here are the contents for the hello-world
example::

    name: node-hello-world
    description: This chute demonstrates a simple web service.
    source:
      type: git
      url: https://github.com/ParadropLabs/node-hello-world
    type: light
    use: node
    command: node index.js
    config:
      web:
        port: 3000

Most of these fields are self-explanatory and covered in the
:doc:`introduction` section.

**type: light**

This indicates that we are building a *light* chute as opposed
to a *normal* chute, which would require a Dockerfile be present.

**use: node**

This indicates that we are using the *node* base image for this
chute.  You should choose the base image appropriate for your
project.  Examples of supported images are *node* and *python2*.

This is handled in an interesting way by ParaDrop. ParaDrop does
not use one single *node* image. Rather, the execution engine
considers the architecture of the underlying hardware and uses
a *node* image built for that architecture.

**command: node index.js**

This line indicates the command for starting your application.  You can
either specify it this way, as a string with spaces between the
parameters, or you can use a list of strings.  The latter format would
be particularly useful if your parameters include spaces.  Here is an
example::

    command:
      - node
      - index.js

Persistent Data
-----------------------

Each running chute has a persistent data storage that is not visible
to other chutes.  By default the persistent data directory is named
"/data" inside the chute's filesystem.  Files stored in this directory
will remain when upgrading or downgrading the chute and are only removed
when uninstalling the chute.
