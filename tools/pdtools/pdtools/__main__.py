"""
Paradrop command line utility.

Two guiding principles were used in the design of the Paradrop command
line utility.

* The command tree should be relatively flat for easy discoverability.
Commands are grouped into a few cohesive modules (chute, cloud, node,
and store).  All of the commands in the cloud module make use of the
cloud controller API, for example. There are no further subgroups under
these top-level groups, which means that `pdtools cloud --help` lists
all relevant commands.

* Commands should be self-evident in their effect. All command names
begin with a verb. Commands that begin with "list-" can be expected
to produce a table of output; commands that begin with "create-" can
be expected to result in the creation of a new resource; and so on.
Although "describe-" is a bit verbose, it conveys a sense that this
command returns everything one needs to know about an object in a way that
"get" does not. It is possible to enable tab completion when pdtools
is installed as a system package.

To enable tab completion, add the following line to your .bashrc file:

    eval "$(_PDTOOLS_COMPLETE=source pdtools)"
"""
import os

import click

# Deprecated command groups to be removed prior to 1.0 release
from . import device
from . import groups
from . import routers

# Command groups
from . import chute
from . import cloud
from . import node
from . import store
from . import wizard


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
groups.register_commands(root)

# Command groups
root.add_command(chute.root)
root.add_command(cloud.root)
root.add_command(node.root)
root.add_command(store.root)
root.add_command(wizard.root)


def main():
    """
    Entry point for the pdtools Python package.
    """
    root()


if __name__ == "__main__":
    main()
