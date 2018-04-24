Getting Started with Go
=======================

This tutorial will teach you how to build a "Hello, World!" chute
using Go.

Prerequisites
-------------

Make sure you have Go installed as well as ParaDrop pdtools (v0.11.2
or newer).

::

    pip install pdtools~=0.11.2

Set up
------

Make a new directory.

::

    mkdir go-hello-world
    cd go-hello-world

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

    name: go-hello-world
    description: Hello World chute for ParaDrop using Go.
    type: light
    image: go
    command: app

The end result should be a paradrop.yaml file similar to the following.

::

    command: app
    config: {}
    description: Hello World chute for ParaDrop using Go.
    name: go-hello-world
    type: light
    use: go
    version: 1

Develop the Application
-----------------------

Create a file name ``main.go`` with the following code.

::

    package main

    import (
        "fmt"
        "net/http"
    )

    func GetIndex(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hello, World!\n")
    }

    func main() {
        fmt.Println("Listening on :8000")
        http.HandleFunc("/", GetIndex)
        http.ListenAndServe(":8000", nil)
    }

Run the application locally with the following command.

::

    go run main.go

Then load ``http://localhost:8000/`` in a web browser to see the result.

Wrap Up
-------

The web server in this application listens on port 8000. We need to
include that information in the paradrop.yaml file as well. Use the
following command to alter the configuration file.

::

    python -m pdtools chute set config.web.port 8000

After that, you can continue developing the chute and install it
on a ParaDrop node.

::

    python -m pdtools node --target=<node address> install-chute
