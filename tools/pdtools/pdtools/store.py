import click
import operator
import os
import time
import yaml

from . import util
from .chute import chute_find_field, chute_resolve_source
from .controller_client import ControllerClient


@click.group('store')
@click.pass_context
def root(ctx):
    """
    Publish and install from the public chute store.

    By default the cloud controller is assumed to be paradrop.org. This
    can be configured through the environment variable PDSERVER_URL.

    It is recommended that you log in with the cloud login command before
    using the store commands.
    """
    pass


@root.command('create-version')
@click.pass_context
def create_version(ctx):
    """
    Push a new version of the chute to the store.
    """
    if not os.path.exists("paradrop.yaml"):
        raise Exception("No paradrop.yaml file found in working directory.")

    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    name = chute_find_field(chute, 'name')
    source = chute_find_field(chute, 'source')
    config = chute.get('config', {})

    chute_resolve_source(source, config)

    client = ControllerClient()
    result = client.find_chute(name)
    if result is None:
        raise Exception("Could not find ID for chute {} - is it registered?".format(name))

    result = client.create_version(name, config)
    click.echo(util.format_result(result))
    return result


@root.command('describe-chute')
@click.argument('name')
@click.pass_context
def describe_chute(ctx, name):
    """
    Show detailed information about a chute in the store.

    NAME must be the name of a chute in the store.
    """
    client = ControllerClient()
    result = client.find_chute(name)
    click.echo(util.format_result(result))
    return result


@root.command('help')
@click.pass_context
def help(ctx):
    """
    Show this message and exit.
    """
    click.echo(ctx.parent.get_help())


@root.command('install-chute')
@click.argument('chute')
@click.argument('node')
@click.option('--follow', '-f',
        help='Follow chute updates.', is_flag=True)
@click.option('--version', '-v',
        help='Version of the chute to install.')
@click.pass_context
def install_chute(ctx, chute, node, follow, version):
    """
    Install a chute from the store.

    CHUTE must be the name of a chute in the store. NODE must be the
    name of a node that you control.
    """
    client = ControllerClient()
    result = client.install_chute(chute, node, select_version=version)
    click.echo(util.format_result(result))

    if follow:
        result2 = client.follow_chute(chute, node)
        click.echo(util.format_result(result2))

    click.echo("Streaming messages until the update has completed.")
    click.echo("Ending output with Ctrl+C will not cancel the update.\n")

    ctx.invoke(watch_update_messages, node_id=result['router_id'], update_id=result['_id'])
    return result


@root.command('list-chutes')
@click.pass_context
def list_chutes(ctx):
    """
    List chutes in the store that you own or have access to.
    """
    client = ControllerClient()
    result = client.list_chutes()
    if len(result) > 0:
        click.echo("Name                             Ver Description")
    for chute in sorted(result, key=operator.itemgetter('name')):
        # Show the summary if available. This is intended to be
        # a shorter description than the description field.
        summary = chute.get('summary', None)
        if summary is None:
            summary = chute.get('description', '')
        click.echo("{:32s} {:3d} {}".format(chute['name'],
            chute['current_version'], summary))
    return result


@root.command('list-versions')
@click.argument('name')
@click.pass_context
def list_versions(ctx, name):
    """
    List versions of a chute in the store.

    NAME must be the name of a chute in the store.
    """
    client = ControllerClient()
    result = client.list_versions(name)
    if len(result) > 0:
        click.echo("Version GitCheckout")
    for version in sorted(result, key=operator.itemgetter('version')):
        try:
            code = version['config']['download']['checkout']
        except:
            code = "N/A"
        click.echo("{:7s} {}".format(str(version['version']), code))
    return result


@root.command()
@click.pass_context
@click.option('--public/--not-public', default=False,
        help='List the chute publicly for other users to download.')
def register(ctx, public):
    """
    Register a chute with the store.

    The chute information including name will be taken from the
    paradrop.yaml file in the current working directory.  If you
    receive an error, it may be that a chute with the same name is
    already registered.
    """
    if not os.path.exists("paradrop.yaml"):
        raise Exception("No paradrop.yaml file found in working directory.")

    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    name = chute_find_field(chute, 'name')
    description = chute_find_field(chute, 'description')

    click.echo("Name: {}".format(name))
    click.echo("Description: {}".format(description))
    click.echo("Public: {}".format(public))
    click.echo("")

    prompt = "Ready to send this information to {} (Y/N)? ".format(
            ctx.obj['pdserver_url'])
    if click.confirm(prompt):
        client = ControllerClient()
        result = client.create_chute(name, description, public=public)
        click.echo(util.format_result(result))
    else:
        click.echo("Operation cancelled.")


@root.command('watch-update-messages')
@click.argument('node_id')
@click.argument('update_id')
@click.option('--interval', type=float, default=0.2, help='Interval to check for new messages')
@click.pass_context
def watch_update_messages(ctx, node_id, update_id, interval):
    """
    Stream log messages from an in-progress update.

    NODE must be the name or ID of a node that you control.  UPDATE_ID must be
    the ID associated with an in-progress update.
    """
    client = ControllerClient()

    displayed = set()
    while True:
        update = client.find_update(node_id, update_id)

        result = client.list_update_messages(node_id, update_id)
        for line in result:
            if line['_id'] not in displayed:
                click.echo(line['message'])
                displayed.add(line['_id'])

        if update['completed']:
            break
        time.sleep(interval)
