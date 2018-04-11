import getpass
from pprint import pprint

import builtins
import click

from . import util
from .controller_client import ControllerClient


@click.group('cloud')
@click.pass_context
def root(ctx):
    """
    Access services provided by a cloud controller
    """
    pass


@root.command('claim-node')
@click.argument('token')
@click.pass_context
def claim_node(ctx, token):
    """
    Take ownership of a node by using a claim token.
    """
    client = ControllerClient()
    result = client.claim_node(token)
    if result is not None:
        print("Claimed node with name {}".format(result['name']))
    else:
        print("No node was found with that claim token.")
    return result


@root.command('create-node')
@click.argument('name')
@click.option('--orphaned/--not-orphaned', default=False)
@click.option('--claim', default=None)
@click.pass_context
def create_node(ctx, name, orphaned, claim):
    """
    Create a new node to be tracked by the controller.
    """
    client = ControllerClient()
    result = client.create_node(name, orphaned=orphaned, claim=claim)
    pprint(result)


@root.command('delete-node')
@click.argument('name')
@click.pass_context
def delete_node(ctx, name):
    """
    Delete a node that is tracked by the controller.
    """
    client = ControllerClient()
    result = client.delete_node(name)
    pprint(result)


@root.command('describe-node')
@click.argument('name')
@click.pass_context
def describe_node(ctx, name):
    """
    Get detailed information about an existing node.
    """
    client = ControllerClient()
    result = client.find_node(name)
    pprint(result)


@root.command('edit-node-description')
@click.argument('name')
@click.pass_context
def edit_node_description(ctx, name):
    """
    Interactively edit the node description and save.
    """
    client = ControllerClient()
    node = client.find_node(name)
    if node is None:
        click.echo("Node {} was not found.".format(name))
        return

    description = util.open_text_editor(node.get('description', ''))
    if description is None:
        click.echo("No change made.")
    else:
        node['description'] = description
        result = client.save_node(node)
        pprint(result)


@root.command('group-add-node')
@click.argument('group')
@click.argument('node')
@click.pass_context
def group_add_node(ctx, group, node):
    """
    Add a node to a group for other members to access.
    """
    client = ControllerClient()
    result = client.group_add_node(group, node)
    pprint(result)


@root.command('help')
@click.pass_context
def help(ctx):
    """
    Show this message and exit
    """
    click.echo(ctx.parent.get_help())


@root.command('list-groups')
@click.pass_context
def list_groups(ctx):
    """
    List groups that you belong to.
    """
    client = ControllerClient()
    result = client.list_groups()
    pprint(result)


@root.command('list-nodes')
@click.pass_context
def list_nodes(ctx):
    """
    List nodes that you own or have access to.
    """
    client = ControllerClient()
    result = client.list_nodes()
    if len(result) > 0:
        print("Name             Online Version Description")
    else:
        print("No nodes were found.")
    for node in result:
        description = node.get('description', '')
        version = node.get('platform_version', 'unknown').split('+')[0]
        print("{name:16s} {online!s:6s} {0:7s} {1}".format(version, description, **node))
    return result


@root.command('login')
@click.pass_context
def login(ctx):
    """
    Interactively login to your user account on the controller.
    """
    client = ControllerClient()
    token = client.login()
    if token is None:
        click.echo("Login attempt failed.")
        return False
    else:
        click.echo("Login successful.")
        return True


@root.command('logout')
@click.pass_context
def logout(ctx):
    """
    Log out by removing stored credentials.
    """
    client = ControllerClient()
    removed = client.logout()
    click.echo("Removed {} token(s).".format(removed))


@root.command('register')
@click.pass_context
def register(ctx):
    """
    Interactively create an account on the controller.
    """
    name = builtins.input("Name: ")
    email = builtins.input("Email: ")
    password = getpass.getpass("Password: ")
    password2 = getpass.getpass("Confirm password: ")

    client = ControllerClient()
    result = client.create_user(name, email, password, password2)

    retval = None

    if 'message' in result:
        click.echo(result['message'])

    if 'token' in result:
        click.echo("The account registration was successful. "
                   "Please check your email and verify the account "
                   "before attempting to log in and use any other "
                   "pdtools cloud commands.")
        retval = email

    if 'errors' in result:
        for key, value in result['errors'].iteritems():
            if 'message' in value:
                click.echo(value['message'])

    return retval


@root.command('rename-node')
@click.argument('name')
@click.argument('new-name')
@click.pass_context
def rename_node(ctx, name, new_name):
    """
    Change the name of a node.
    """
    client = ControllerClient()
    node = client.find_node(name)
    if node is None:
        click.echo("Node {} was not found.".format(name))
        return
    node['name'] = new_name
    result = client.save_node(node)
    pprint(result)
