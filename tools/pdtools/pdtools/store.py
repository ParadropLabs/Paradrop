import builtins
import click
import operator
import os
import yaml

from pprint import pprint

from .chute import chute_resolve_source
from .controller_client import ControllerClient


@click.group('store')
@click.pass_context
def root(ctx):
    """
    Interact with the public chute store.
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
    pprint(result)


@root.command('describe-chute')
@click.argument('name')
@click.pass_context
def describe_chute(ctx, name):
    """
    Show detailed information about a chute in the store.
    """
    client = ControllerClient()
    result = client.find_chute(name)
    pprint(result)


@root.command('help')
@click.pass_context
def help(ctx):
    """
    Show this message and exit
    """
    click.echo(ctx.parent.get_help())


@root.command('install-chute')
@click.argument('chute')
@click.argument('node')
@click.option('--version', '-v', help='Version to install')
@click.pass_context
def install_chute(ctx, chute, node, version):
    """
    Install a chute from the store.
    """
    client = ControllerClient()
    result = client.install_chute(chute, node, select_version=version)
    pprint(result)


@root.command('list-chutes')
@click.pass_context
def list_chutes(ctx):
    """
    List chutes in the store that you own or have access to.
    """
    client = ControllerClient()
    result = client.list_chutes()
    click.echo("Name                             Ver Description")
    for chute in sorted(result, key=operator.itemgetter('name')):
        click.echo("{name:32s} {current_version:3d} {description}".format(**chute))


@root.command('list-versions')
@click.argument('name')
@click.pass_context
def list_versions(ctx, name):
    """
    List versions of a chute in the store.
    """
    client = ControllerClient()
    result = client.list_versions(name)
    click.echo("Version GitCheckout")
    for version in sorted(result, key=operator.itemgetter('version')):
        try:
            code = version['config']['download']['checkout']
        except:
            code = "N/A"
        print("{:7s} {}".format(str(version['version']), code))


@root.command()
@click.pass_context
@click.option('--public/--not-public', default=False)
def register(ctx, public):
    """
    Register a chute with the store.
    """
    if not os.path.exists("paradrop.yaml"):
        raise Exception("No paradrop.yaml file found in working directory.")

    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    name = chute_find_field(chute, 'name')
    description = chute_find_field(chute, 'description')

    print("Name: {}".format(name))
    print("Description: {}".format(description))
    print("Public: {}".format(public))
    print("")

    prompt = "Ready to send this information to {} (Y/N)? ".format(
            ctx.obj['pdserver_url'])
    response = builtins.input(prompt)
    print("")

    if response.upper().startswith("Y"):
        client = ControllerClient()
        result = client.create_chute(name, description, public=public)
        pprint(result)
    else:
        print("Operation cancelled.")
