import builtins
import click
import json
import operator
import os

import git
import yaml

from .controller_client import ControllerClient
from .helpers.chute import build_chute
from .util import update_object


def chute_find_field(chute, key, default=Exception):
    """
    Find a field in a chute definition loading from a paradrop.yaml file.
    """
    if key in chute:
        return chute[key]
    elif 'config' in chute and key in chute['config']:
        return chute['config'][key]
    elif isinstance(default, type):
        raise default("{} field not found in chute definition.".format(key))
    else:
        return default


def chute_resolve_source(source, config):
    """
    Resolve the source section from paradrop.yaml to store configuration.

    If git/http, add an appropriate download section to the chute
    configuration. For git repos, we also identify the latest commit and add
    that to the download information. If type is inline, add a dockerfile
    string field to the chute and no download section.
    """
    if 'type' not in source:
        raise Exception("Source type not specified for chute.")

    source_type = source['type']
    if source_type == 'http':
        config['download'] = {
            'url': source['url']
        }

    elif source_type == 'git':
        repo = git.Repo('.')
        config['download'] = {
            'url': source['url'],
            'checkout': str(repo.head.commit)
        }

    elif source_type == 'inline':
        with open('Dockerfile', 'r') as dockerfile:
            config['dockerfile'] = dockerfile.read()

    else:
        raise Exception("Invalid source type {}".format(source_type))


@click.group('chute')
@click.pass_context
def root(ctx):
    """
    Utilities for developing chutes.

    These commands all operate on a chute project in the current working
    directory.  Remember, that all chutes must have a paradrop.yaml file
    in the top-level directory.  You can create one interactively with
    the initialize command.
    """
    pass


@root.command('add-wifi-ap')
@click.argument('essid')
@click.option('--password', default=None,
        help='Password for the network, must be at least 8 characters if specified.')
@click.option('--force', default=False, is_flag=True,
        help='Overwrite an existing section in the configuration file.')
@click.pass_context
def add_wifi_ap(ctx, essid, password, force):
    """
    Add a WiFi AP to the chute configuration.

    ESSID must be between 1 and 32 characters in length.  Spaces are
    allowed if you enclose the argument in quotation marks.
    """
    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    # Make sure the config.net section exists.
    net = update_object(chute, 'config.net')

    # Only support adding the first Wi-Fi interface for now.
    if 'wifi' in net and not force:
        click.echo("Wi-Fi interface already exists in paradrop.yaml.")
        click.echo("Please edit the file directly to make changes.")
        return

    net['wifi'] = {
        'type': 'wifi',
        'intfName': 'wlan0',
        'dhcp': {
            'lease': '12h',
            'start': 4,
            'limit': 250
        },
        'ssid': essid,
        'options': {
            'isolate': False,
            'hidden': False
        }
    }

    # Minimum password length is part of the standard.
    if password is not None:
        if len(password) < 8:
            print("Wi-Fi password must be at least 8 characters.")
            return
        net['wifi']['key'] = password

    with open('paradrop.yaml', 'w') as output:
        yaml.safe_dump(chute, output, default_flow_style=False)


@root.command('export-configuration')
@click.option('--format', '-f', default='json',
        help="Format (json or yaml)")
@click.pass_context
def export_configuration(ctx, format):
    """
    Export chute configuration in JSON or YAML format.

    The configuration format used by the cloud API is slightly different
    from the paradrop.yaml file. This command can export a JSON object in
    a form suitable for installing the chute through the cloud API.

    The config object will usually be used in an envelope like the following:
    {
      "updateClass": "CHUTE",
      "updateType": "update",
      "config": { config-object }
    }
    """
    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    if 'source' not in chute:
        click.echo("Error: source section missing in paradrop.yaml")
        return

    config = chute.get('config', {})

    config['name'] = chute['name']
    config['version'] = chute.get('version', 1)

    chute_resolve_source(chute['source'], config)

    format = format.lower()
    if format == "json":
        click.echo(json.dumps(config, sort_keys=True, indent=2))
    elif format == "yaml":
        click.echo(yaml.safe_dump(config, default_flow_style=False))
    else:
        click.echo("Unrecognized format: {}".format(format))


@root.command('initialize')
@click.pass_context
def initialize(ctx):
    """
    Interactively create a paradrop.yaml file.
    """
    chute = build_chute()
    with open("paradrop.yaml", "w") as output:
        yaml.safe_dump(chute, output, default_flow_style=False)

    # If this is a node.js chute, generate a package.json file from the
    # information that the user provided.
    if chute.get('use', None) == 'node':
        if not os.path.isfile('package.json'):
            data = {
                'name': chute['name'],
                'version': '1.0.0',
                'description': chute['description']
            }
            with open('package.json', 'w') as output:
                json.dump(data, output, sort_keys=True, indent=2)


@root.command('set')
@click.argument('path')
@click.argument('value')
@click.pass_context
def set_config(ctx, path, value):
    """
    Set a value in the paradrop.yaml file.

    PATH must be a dot-separated path to a value in the paradrop.yaml
    file, such as "config.web.port". VALUE will be interpreted as a
    string, numeric, or boolean type as appropriate.

    Changing values inside a list is not currently supported.  For that
    you will need to edit the file directly.

    Example: set config.web.port 80
    """
    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    # Empty paradrop.yaml file?
    if chute is None:
        chute = {}

    # Calling yaml.safe_load on the value does a little type interpretation
    # (e.g. numeric vs. string) and allows the user to directly set lists and
    # other structures.
    value = yaml.safe_load(value)

    def set_value(parent, key, created):
        if created:
            click.echo("Creating new field {} = {}".format(path, value))
        else:
            current = parent[key]
            click.echo("Changing {} from {} to {}".format(path, current, value))

        parent[key] = value

    update_object(chute, path, set_value)

    with open('paradrop.yaml', 'w') as output:
        yaml.safe_dump(chute, output, default_flow_style=False)
