ParaDrop API Tests
==================

The tests in this directory are designed to exercise a live installation of
ParaDrop through its public API.

Prerequisites
-------------

You will need pyresttests installed on the machine that will be running the
tests, e.g. your development machine.

    sudo pip install pyresttests

Running the Tests
-----------------

These tests require a running instance of ParaDrop. It is best to run on
hardware in order to exercise the full range of functionality, but a VM could
also be used. You will need to identify the address of the ParaDrop host to be
the target of the tests. In the example below, the ParaDrop box is connected to
a wired network with address 10.42.0.10.

    pyresttests http://10.42.0.10 all.yaml

Adding New Tests
----------------

Please refer to the pyresttest documentation
(https://github.com/svanoort/pyresttest). It has many advanced features for
variables, extraction, validation, etc. Tests should be organized into
different YAML files based on the features or modules that they exercise
and added as imports to the all.yaml file. This leaves some flexibility
for us to create custom subsets of tests that apply to certain platforms.
