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
        yaml.dump(chute, output, default_flow_style=False)

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
