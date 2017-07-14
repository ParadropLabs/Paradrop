"""
Paradrop command line utility.

Environment Variables:
    PDSERVER_URL    Paradrop controller URL [default: https://paradrop.org].
"""
import os

import click

from . import device
from . import routers


PDSERVER_URL = os.environ.get("PDSERVER_URL", "https://paradrop.org")


@click.group()
@click.pass_context
def root(ctx):
    """
    Paradrop command line utility.

    Environment Variables
        PDSERVER_URL    Paradrop controller URL
    """
    ctx.obj = {
        'pdserver_url': PDSERVER_URL
    }


root.add_command(device.device)
root.add_command(routers.routers)


if __name__ == "__main__":
    root()
