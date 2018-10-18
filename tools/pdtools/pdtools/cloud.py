import getpass

import builtins
import click

from . import util
from .controller_client import ControllerClient


@click.group('cloud')
@click.pass_context
def root(ctx):
    """
    Access services provided by a cloud controller.

    By default the cloud controller is assumed to be paradrop.org. This
    can be configured through the environment variable PDSERVER_URL.
    """
    pass


@root.command('claim-node')
@click.argument('token')
@click.option('--name', '-n', default=None, help='Name of the node')
@click.pass_context
def claim_node(ctx, token, name):
    """
    Take ownership of a node by using a claim token.

    TOKEN is a hard-to-guess string that the previous owner would have
    configured when setting the node's status as orphaned.
    """
    client = ControllerClient()
    result = client.claim_node(token, name=name)
    if result is not None and 'name' in result:
        click.echo("Claimed node with name {}".format(result['name']))
    elif result is not None and 'message' in result:
        click.echo(result['message'])
    else:
        click.echo("No node was found with that claim token.")
    return result


@root.command('create-node')
@click.argument('name')
@click.option('--orphaned/--not-orphaned', default=False,
        help='Allow another user to claim the node.')
@click.option('--claim', default=None,
        help='Claim token required to claim the node.')
@click.pass_context
def create_node(ctx, name, orphaned, claim):
    """
    Create a new node to be tracked by the controller.

    NAME must be unique among the nodes that you own and may only consist
    of lowercase letters, numbers, and hyphens. It must also begin with
    a letter.
    """
    client = ControllerClient()
    result = client.create_node(name, orphaned=orphaned, claim=claim)
    click.echo(util.format_result(result))
    return result


@root.command('delete-node')
@click.argument('name')
@click.pass_context
def delete_node(ctx, name):
    """
    Delete a node that is tracked by the controller.

    NAME must be the name of a node that you own.
    """
    client = ControllerClient()
    result = client.delete_node(name)
    click.echo(util.format_result(result))
    return result


@root.command('describe-node')
@click.argument('name')
@click.pass_context
def describe_node(ctx, name):
    """
    Get detailed information about an existing node.

    NAME must be the name of a node that you own.
    """
    client = ControllerClient()
    result = client.find_node(name)
    click.echo(util.format_result(result))
    return result


@root.command('edit-node-description')
@click.argument('name')
@click.pass_context
def edit_node_description(ctx, name):
    """
    Interactively edit the node description and save.

    NAME must be the name of a node that you own.

    Open the text editor specified by the EDITOR environment variable
    with the current node description. If you save and exit, the changes
    will be applied to the node.
    """
    client = ControllerClient()
    node = client.find_node(name)
    if node is None:
        click.echo("Node {} was not found.".format(name))
        return

    description = click.edit(node.get('description', ''))
    if description is None:
        click.echo("No change made.")
    else:
        node['description'] = description
        result = client.save_node(node)
        click.echo(util.format_result(result))
        return result


@root.command('group-add-node')
@click.argument('group')
@click.argument('node')
@click.pass_context
def group_add_node(ctx, group, node):
    """
    Add a node to a group for other members to access.

    GROUP must be the string ID of a group. NODE must be the name of a
    node that you control.
    """
    client = ControllerClient()
    result = client.group_add_node(group, node)
    click.echo(util.format_result(result))
    return result


@root.command('help')
@click.pass_context
def help(ctx):
    """
    Show this message and exit.
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
    click.echo(util.format_result(result))
    return result


@root.command('list-nodes')
@click.pass_context
def list_nodes(ctx):
    """
    List nodes that you own or have access to.
    """
    client = ControllerClient()
    result = client.list_nodes()
    if len(result) > 0:
        click.echo("Name             Online Version Description")
    else:
        click.echo("No nodes were found.")
    for node in result:
        description = node.get('description', '')
        version = node.get('platform_version', 'unknown').split('+')[0]
        click.echo("{name:16s} {online!s:6s} {0:7s} {1}".format(version, description, **node))
    return result


@root.command('login')
@click.pass_context
def login(ctx):
    """
    Interactively login to your user account on the controller.

    Authenticate with the controller using account credentials that you
    created either through the website or with the register command.
    Typically, the username will be your email address.
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
    Log out and remove stored credentials.
    """
    client = ControllerClient()
    removed = client.logout()
    click.echo("Removed {} token(s).".format(removed))
    return removed


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

    NAME must be the name of a node that you control. NEW_NAME is the
    desired new name. It must adhere to the same naming rules as for
    the create-node command, namely, it must begin with a letter and
    consist of only lowercase letters, numbers, and hyphen.
    """
    client = ControllerClient()
    node = client.find_node(name)
    if node is None:
        click.echo("Node {} was not found.".format(name))
        return
    node['name'] = new_name
    result = client.save_node(node)
    click.echo(util.format_result(result))
    return result
