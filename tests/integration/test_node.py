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
import yaml
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


def find_one_chute():
    result = invoke("node list-chutes")
    chutes = yaml.safe_load(result.output)
    if not isinstance(chutes, list) or len(chutes) == 0:
        raise unittest.SkipTest("No chutes installed on test node")
    return chutes[0]


@skip_if_no_target
def test_connect_snap_interfaces():
    result = invoke("node connect-snap-interfaces")
    assert result.exit_code == 0


@skip_if_no_target
def test_create_user():
    result = invoke("node create-user info@paradrop.io")
    assert result.exit_code == 0


@skip_if_no_target
def test_describe_audio():
    result = invoke("node describe-audio")
    assert result.exit_code == 0
    assert "server_name: pulseaudio" in result.output


@skip_if_no_target
def test_describe_chute():
    chute = find_one_chute()
    result = invoke("node describe-chute " + chute['name'])
    assert result.exit_code == 0
    assert "name: {}".format(chute['name']) in result.output


@skip_if_no_target
def test_describe_chute_cache():
    chute = find_one_chute()
    result = invoke("node describe-chute-cache " + chute['name'])
    assert result.exit_code == 0
    assert "networkInterfaces:" in result.output


@skip_if_no_target
def test_describe_chute_configuration():
    chute = find_one_chute()
    result = invoke("node describe-chute-configuration " + chute['name'])
    assert result.exit_code == 0
    assert "name: {}".format(chute['name']) in result.output


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


@skip_if_no_target
def test_list_changes():
    result = invoke("node list-changes")
    assert result.exit_code == 0
    changes = yaml.safe_load(result.output)
    assert changes is None or isinstance(changes, list)


@skip_if_no_target
def test_list_chutes():
    result = invoke("node list-chutes")
    assert result.exit_code == 0
    chutes = yaml.safe_load(result.output)
    assert chutes is None or isinstance(chutes, list)


@skip_if_no_target
def test_list_devices():
    result = invoke("node list-devices")
    assert result.exit_code == 0
    devices = yaml.safe_load(result.output)
    assert devices is None or isinstance(devices, list)


@skip_if_no_target
def test_list_ssh_keys():
    result = invoke("node list-ssh-keys")
    assert result.exit_code == 0
    keys = yaml.safe_load(result.output)
    assert keys is None or isinstance(keys, list)


@skip_if_no_target
def test_restart_chute():
    chute = find_one_chute()
    result = invoke("node restart-chute " + chute['name'])
    assert result.exit_code == 0
