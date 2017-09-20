"""
Paradrop command line utility.

Environment Variables:
    PDSERVER_URL    Paradrop controller URL [default: https://paradrop.org].
"""
import os

import click

from . import chute
from . import device
from . import routers
from . import store


PDSERVER_URL = os.environ.get("PDSERVER_URL", "https://paradrop.org")


@click.group()
@click.pass_context
def root(ctx):
    """
    Paradrop command line utility.

    Environment Variables
        PDSERVER_URL    Paradrop controller URL
    """
    # Options can be parsed from PDTOOLS_* environment variables.
    ctx.auto_envvar_prefix = 'PDTOOLS'

    # Respond to both -h and --help for all commands.
    ctx.help_option_names = ['-h', '--help']

    ctx.obj = {
        'pdserver_url': PDSERVER_URL
    }


root.add_command(chute.chute)
root.add_command(device.device)
root.add_command(routers.routers)
root.add_command(store.store)


def main():
    """
    Entry point for the pdtools Python package.
    """
    root()


if __name__ == "__main__":
    main()
