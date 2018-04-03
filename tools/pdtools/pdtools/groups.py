import click

from .comm import pdserver_request


@click.command('list-groups')
@click.pass_context
def list_groups(ctx):
    """
    (deprecated) List user groups.

    Please use `pdtools cloud list-groups`.
    """
    url = ctx.obj['pdserver_url'] + "/api/groups"
    result = pdserver_request('GET', url)
    groups = result.json()

    for group in groups:
        print("{} {}".format(group['_id'], group['name']))

        print("  Users:")
        for user_id in group['users']:
            print("    {}".format(user_id))

        print("  Routers:")
        for router_id in group['routers']:
            print("    {}".format(router_id))


@click.group()
@click.pass_context
@click.argument('group_id')
def group(ctx, group_id):
    """
    (deprecated) Manage a user group.

    These commands are deprecated. Please use the equivalent commands under
    `pdtools cloud --help`.
    """
    ctx.obj['group_url'] = ctx.obj['pdserver_url'] + "/api/groups/{}".format(group_id)


@group.command('add-router')
@click.pass_context
@click.argument('router_id')
def add_router(ctx, router_id):
    """
    Add a router to the group.
    """
    url = ctx.obj['group_url'] + "/addRouter"
    data = {
        'router_id': router_id
    }
    result = pdserver_request('POST', url, json=data)
    if result.ok:
        print("Added router.")
    else:
        print("There was an error adding the router.")


def register_commands(root):
    """
    Register commands in this module.
    """
    root.add_command(list_groups)
    root.add_command(group)
