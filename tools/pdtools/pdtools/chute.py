import click
import json
import os
import yaml

from .helpers.chute import build_chute
from .store import chute_resolve_source
from .util import update_object


@click.group()
@click.pass_context
def chute(ctx):
    """
    Sub-tree for building chutes.
    """
    pass


@chute.command('create-wifi-interface')
@click.pass_context
@click.argument('essid')
@click.option('--password', default=None)
@click.option('--force', default=False, is_flag=True)
def create_wifi_interface(ctx, essid, password, force):
    """
    Add a Wi-Fi interface (AP mode) to the chute configuration.
    """
    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    # Make sure the config.net section exists.
    net = update_object(chute, 'config.net')

    # Only support adding the first Wi-Fi interface for now.
    if 'wifi' in net and not force:
        print("Wi-Fi interface already exists in paradrop.yaml.")
        print("Please edit the file directly to make changes.")
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


@chute.command('cloud-config')
@click.pass_context
def cloud_config(ctx):
    """
    Produce a JSON config object that can be used with cloud API.

    The configuration format used by the cloud API is slightly different
    from the paradrop.yaml file. This command dumps a JSON object in
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
        print("Error: source section missing in paradrop.yaml")
        return

    config = chute.get('config', {})

    config['name'] = chute['name']
    config['version'] = chute.get('version', 1)

    chute_resolve_source(chute['source'], config)

    print(json.dumps(config, sort_keys=True, indent=2))


@chute.command()
@click.pass_context
def init(ctx):
    """
    Interactively create a paradrop.yaml file.

    This will ask the user some questions and then writes a paradrop.yaml file.
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


@chute.command()
@click.pass_context
@click.argument('path')
@click.argument('value')
def set(ctx, path, value):
    """
    Set a value in the chute configuration file.

    Example: set config.web.port 80
    """
    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    # Calling yaml.safe_load on the value does a little type interpretation
    # (e.g. numeric vs. string) and allows the user to directly set lists and
    # other structures.
    value = yaml.safe_load(value)

    def set_value(parent, key, created):
        if created:
            print("Creating new field {} = {}".format(path, value))
        else:
            current = parent[key]
            print("Changing {} from {} to {}".format(path, current, value))

        parent[key] = value

    update_object(chute, path, set_value)

    with open('paradrop.yaml', 'w') as output:
        yaml.safe_dump(chute, output, default_flow_style=False)
