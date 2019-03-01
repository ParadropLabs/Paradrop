# Paradrop Developer Tools

[![Documentation Status](https://readthedocs.org/projects/paradrop/badge/?version=latest)](https://readthedocs.org/projects/paradrop/?badge=latest)

The Paradrop developer tools (`pdtools`) make it easy to interact with
the Paradrop edge and cloud APIs. Use it to configure or install software
on a Paradrop node or develop and release your own applications, called
"chutes", to the Paradrop Chute Store.  `pdtools` can be used as a command
line utility and can also be imported into Python code as a library.

## What is Paradrop?

Paradrop is a software platform for edge computing that brings the cloud
closer to home by enabling applications to exist on networking equipment
such as Wi-Fi routers.

By running services closer to data sources and mobile devices,
applications can take advantage of low network latency and make efficient
use of bandwidth.  Additionally, services running on Paradrop can protect
the privacy of users by processing sensitive data near its source rather
than transmitting it over the wide area network. Some services can even
remain functional when the Internet connection is down.

## Installation

The latest version is available on [PyPi](https://pypi.org/project/pdtools/).
Install it with `pip`:

    pip install pdtools

Using the command above will install `pdtools` as a local Python
module. On Linux, you can also install `pdtools` as a global package
to make it available as a command. That means you will be able to use
`pdtools` in your shell instead of typing `python -m pdtools`.

    sudo pip install pdtools

## Usage

`pdtools` includes an extensive command line utility for interacting with
Paradrop nodes and our cloud controller. You can explore the commands
available with the `-h` or `--help` flags.

    python -m pdtools --help

Use the interactive tool to begin developing a new chute:

    python -m pdtools chute initialize

Install a chute on a node if you know its IP address:

    python -m pdtools node --target <node-ip-address> install-chute

List the chutes installed on a node:

    python -m pdtools node --target <node-ip-address> list-chutes

List chutes available in the Paradrop Chute Store:

    python -m pdtools store list-chutes

Install a chute on a node from the chute store. Here you must use the
name assigned to the node on paradrop.org:

    python -m pdtools store install-chute <chute-name> <node-name>

All of the functions available through the command line are also
available for scripting in your own Python code. For example,
the following Python code queries a node for the list of chutes
installed and then makes a request to remove one of them:

    >>> NODE_ADDRESS = "192.0.2.1" # Use the IP address of your node.
    >>> from pdtools import ParadropClient
    >>> client = ParadropClient(NODE_ADDRESS)
    >>> for chute in client.list_chutes():
    ...     print(chute['name'])
    ...
    node-hello-world
    wiki
    python-hello-world
    sticky-board
    >>> client.remove_chute('node-hello-world')
    {u'change_id': 1}

## Instructions for Maintainers

Use the following commands in the directory containing this file and setup.py
to build the packages:

    python setup.py sdist
    python setup.py bdist_wheel --universal

Use the following command to upload the packages to PyPi:

    twine upload dist/*
