Getting Started with Python
===========================

This tutorial will teach you how to build a "Hello, World!" chute using
Python and Flask.

Prerequisites
-------------

Make sure you have Python 2 installed as well as ParaDrop
pdtools (v0.12.0 or newer).

::

    pip install pdtools~=0.12

Set up
------

Make a new directory.

::

    mkdir python-hello-world
    cd python-hello-world

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

    name: python-hello-world
    description: Hello World chute for ParaDrop using Python.
    type: light
    image: python2
    command: python2 -u main.py

The end result should be a paradrop.yaml file similar to the following.

::

    description: Hello World chute for ParaDrop using Python.
    name: python-hello-world
    services:
      main:
        command: python2 -u main.py
        image: python2
        source: .
        type: light
    version: 1

Install Dependencies
--------------------

We will use pip and virtualenv to manage dependencies for the project.
First set up a virtual enviroment.

::

    virtualenv venv
    source venv/bin/activate

Use the following command to install some dependencies. We will be using
Flask as a simple web server.

::

    pip install Flask==0.12.2

Finally, save the version information to a file called
``requirements.txt``.  When installing the chute, ParaDrop will use
this file to install the same versions of the packages that you used
during development.

::

    pip freeze >requirements.txt

Develop the Application
-----------------------

We indicated that main.py is the entrypoint for the application, so we
will create a file named ``main.py`` and put our code there.

::

    from flask import Flask

    app = Flask(__name__)

    @app.route('/')
    def index():
        return 'Hello, World!'

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)

Run the application locally with the following command.

::

    python main.py

Then load ``http://localhost:5000/`` in a web browser to see the result.

Wrap Up
-------

The web server in this application listens on port 5000. We need to
include that information in the paradrop.yaml file as well. Use the
following command to alter the configuration file.

::

    python -m pdtools chute enable-web-service 5000

After that, you can continue developing the chute and install it
on a ParaDrop node.

::

    python -m pdtools node --target=<node address> install-chute
