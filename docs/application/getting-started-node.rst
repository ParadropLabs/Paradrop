Getting Started with Node.js
============================

This tutorial will teach you how to build a "Hello, World!" chute using
Node.js and Express.

Prerequisites
-------------

Make sure you have Node.js (v6 or newer) installed as well as ParaDrop
pdtools (v0.12.0 or newer).

::

    pip install pdtools~=0.12

Set up
------

Make a new directory.

::

    mkdir node-hello-world
    cd node-hello-world

Create a chute configuration
----------------------------

Use the pdtools interactive initialize command to create a paradrop.yaml
file for your chute.

::

    python -m pdtools chute initialize

Use the following values as suggested responses to the prompts. If
you have a different version of pdtools installed, the prompts may be
slightly different.

::

    name: node-hello-world
    description: Hello World chute for ParaDrop using Node.js.
    type: light
    image: node
    command: node index.js

The end result should be a paradrop.yaml file similar to the following.

::

    description: Hello World chute for ParaDrop using Node.js.
    name: node-hello-world
    services:
      main:
        command: node index.js
        image: node
        source: .
        type: light
    version: 1

The ``pdtools chute init`` command will also create a package.json file
for you if one did not already exist, so there is no need to run ``npm
init`` after running ``pdtools chute init``.

Install Dependencies
--------------------

Use the following command to install some dependencies. We will be using
Express as a simple web server.

The ``--save`` option instructs npm to save the packages to the
package.json file. When installing the chute, ParaDrop will read
package.json to install the same versions of the packages that you used
for development.::

    npm install --save express@^4.16.1

Develop the Application
-----------------------

We indicated that index.js is the entrypoint for the application, so we
will create a file named ``index.js`` and put our code there.

::

    const express = require('express')
    const app = express()

    app.get('/', function (req, res) {
      res.send('Hello, World!')
    })

    app.listen(3000, function() {
      console.log('Listening on port 3000.')
    })

Run the application locally with the following command.

::

    node index.js

Then load ``http://localhost:3000/`` in a web browser to see the result.

Wrap Up
-------

The web server in this application listens on port 3000. We need to
include that information in the paradrop.yaml file as well. Use the
following command to alter the configuration file.

::

    python -m pdtools chute enable-web-service 3000

After that, you can continue developing the chute and install it
on a ParaDrop node.

::

    python -m pdtools node --target=<node address> install-chute
