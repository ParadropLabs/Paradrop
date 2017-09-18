import click
import json
import os
import yaml

from .helpers.chute import build_chute


@click.group()
@click.pass_context
def chute(ctx):
    """
    Sub-tree for building chutes.
    """
    pass


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
                'name': chute['config']['name'],
                'version': '1.0.0',
                'description': chute['description']
            }
            with open('package.json', 'w') as output:
                json.dump(data, output, sort_keys=True, indent=2)


@chute.command()
@click.pass_context
@click.argument('key')
@click.argument('value')
def set(ctx, key, value):
    """
    Set a value in the chute configuration file.

    Example: set config.web.port 80
    """
    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    parts = key.split(".")

    # Calling yaml.safe_load on the value does a little type interpretation
    # (e.g. numeric vs. string) and allows the user to directly set lists and
    # other structures.
    value = yaml.safe_load(value)

    parent = chute
    current = chute
    created = False
    for part in parts:
        if len(part) == 0:
            raise Exception("Key ({}) is invalid".format(key))

        parent = current

        # Create dictionaries along the way if path nodes do not exist,
        # but make note of the fact that the previous value did not exist.
        if part not in parent:
            parent[part] = {}
            created = True

        current = parent[part]

    if created:
        print("Creating new field {} = {}".format(key, value))
    else:
        print("Changing {} from {} to {}".format(key, current, value))

    parent[parts[-1]] = value

    with open('paradrop.yaml', 'w') as output:
        yaml.safe_dump(chute, output, default_flow_style=False)
