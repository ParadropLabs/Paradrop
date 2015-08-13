
Getting Started
====================================

This will quickly take you through the process of bringing up a Hello World chute in a virtual machine on your computer.

*NOTE*: As of release 0.1, pdbuild is built around using Ubuntu. We will eliminate this requirement soon, work arounds can be found at :ref:`no_ubuntu`.

Environment setup
-------------------

.. TODO: remove need to say install pypubsub once fixed.

0. Prerequisites:

   * Packages: Python 2.7, python-pip, python-dev, libffi-dev, libssl-dev
   * PyPI: pex
   * When you install build tools you may have to run: ``sudo pip install pypubsub --allow-external pypubsub``

1. Install our `build tools <https://pypi.python.org/pypi/pdtools>`_ (``pip install pdtools``).
2. Clone our `instance tools <https://github.com/ParadropLabs/Paradrop>`_.
3. Setup instance tools ``pdbuild.sh setup``
4. Boot local testing VM ``pdbuild.sh up``
5. Install instance dependencies ``pdbuild.sh install_deps``
6. Build the tools to go into testing VM ``pdbuild.sh build``
7. Push tools into VM ``pdbuild.sh install`` (NOTE: sometimes this fails, please check :doc:`faq`)
8. Check the installation ``pdbuild.sh check``


Installing chutes
-----------------------

First you must register an account from our CLI: ``paradrop register``.
This will setup a private key on your computer which allows you to access our platform.

* Clone the Paradrop `example apps <https://github.com/ParadropLabs/Example-Apps>`_.

Install **hello-world** chute::

    cd <apps-repo>/hello-world
    paradrop chute install localhost 9999 ./config.yaml
    
    Result:
    ...
    Chute hello-world create success

As a simple use case, **hello-world** starts an nginx server in the chute. To access this, visit ``localhost:9000`` in any web browser, you should see::

    Hello World from Paradrop!

Running ``paradrop chute stop localhost 9999 hello-world`` will stop the chute, if you refresh the webpage, you should no longer see the Hello World message.
