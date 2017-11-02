"""
Paradrop command line utility.

Environment Variables:
    PDSERVER_URL    Paradrop controller URL [default: https://paradrop.org].
"""
import os

import click

from . import chute
from . import device
from . import groups
from . import routers
from . import store


PDSERVER_URL = os.environ.get("PDSERVER_URL", "https://paradrop.org")

CONTEXT_SETTINGS = dict(
    # Options can be parsed from PDTOOLS_* environment variables.
    auto_envvar_prefix = 'PDTOOLS',

    # Respond to both -h and --help for all commands.
    help_option_names = ['-h', '--help'],

    obj = {
        'pdserver_url': PDSERVER_URL
    }
)


@click.group(context_settings=CONTEXT_SETTINGS)
def root():
    """
    Paradrop command line utility.

    Environment Variables
        PDSERVER_URL    ParaDrop controller URL [default: https://paradrop.org]
    """
    pass


root.add_command(chute.chute)
root.add_command(device.device)
root.add_command(routers.routers)
root.add_command(store.store)
groups.register_commands(root)


def main():
    """
    Entry point for the pdtools Python package.
    """
    root()


if __name__ == "__main__":
    main()
