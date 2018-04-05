"""
Paradrop command line utility.

Environment Variables:
    PDSERVER_URL    Paradrop controller URL [default: https://paradrop.org].
"""
import os

import click

# Deprecated command groups to be removed prior to 1.0 release
from . import device
from . import groups
from . import routers
from . import store

# Command groups
from . import chute
from . import cloud
from . import node


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


@root.command('help')
@click.pass_context
def help(ctx):
    """
    Show this message and exit
    """
    click.echo(ctx.parent.get_help())


# Deprecated command groups to be removed prior to 1.0 release
root.add_command(device.device)
root.add_command(routers.routers)
root.add_command(store.store)
groups.register_commands(root)

# Command groups
root.add_command(chute.root)
root.add_command(cloud.root)
root.add_command(node.root)


def main():
    """
    Entry point for the pdtools Python package.
    """
    root()


if __name__ == "__main__":
    main()
