"""
Integration tests for pdtools node commands.

These tests use the click testing module to invoke pdtools node commands
as if they were called from the command line.  These tests will only
run if the PDTOOLS_NODE_TARGET environment variable is set to the IP
address of a node against which we can run the tests.
"""

import os
import unittest

import click
from click.testing import CliRunner

from pdtools.__main__ import root


# Decorator that skips a test if the PDTOOLS_NODE_TARGET environment variable
# is not defined.
skip_if_no_target = unittest.skipUnless(
        'PDTOOLS_NODE_TARGET' in os.environ,
        "requires PDTOOLS_NODE_TARGET environment variable to be set"
)


def invoke(subcommand):
    runner = CliRunner()
    return runner.invoke(root, subcommand.split())


@skip_if_no_target
def test_describe_audio():
    result = invoke("node describe-audio")
    assert result.exit_code == 0
    assert "server_name: pulseaudio" in result.output


@skip_if_no_target
def test_describe_pdconf():
    result = invoke("node describe-pdconf")
    assert result.exit_code == 0
    assert "__PARADROP__" in result.output


@skip_if_no_target
def test_describe_provision():
    result = invoke("node describe-provision")
    assert result.exit_code == 0
    assert "provisioned:" in result.output


@skip_if_no_target
def test_describe_settings():
    result = invoke("node describe-settings")
    assert result.exit_code == 0
    assert "concurrent_builds:" in result.output
