#import getpass
#import operator
#import os
#import tarfile
#import tempfile
#
#import builtins
import click
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
