"""
Paradrop command line utility.

Environment Variables:
    PDSERVER_URL    Paradrop controller URL [default: https://paradrop.org].
"""
import os

import click

from . import chute
from . import device
from . import server
from .config import PDSERVER_URL


@click.group()
@click.pass_context
def root(ctx):
    """
    Paradrop command line utility.

    Environment Variables
        PDSERVER_URL    ParaDrop controller URL [default: https://paradrop.org]
    """
    ctx.obj = {
        'pdserver_url': PDSERVER_URL
    }


root.add_command(chute.chute)
root.add_command(device.device)
root.add_command(server.server)


def main():
    """
    Entry point for the pdtools Python package.
    """
    root()


if __name__ == "__main__":
    main()
