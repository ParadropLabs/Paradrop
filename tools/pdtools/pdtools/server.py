import click

from .comm import pdserver_request


@click.group()
@click.pass_context
def server(ctx):
    """
    Commands to work with the ParaDrop server (controller).
    """
    ctx.obj['routers_url'] = ctx.obj['pdserver_url'] + "/api/routers"


@server.command()
@click.pass_context
def list_routers(ctx):
    """
    List routers.
    """
    url = ctx.obj['routers_url']
    result = pdserver_request('GET', url)
    routers = result.json()

    for router in routers:
        print("{} {} {}".format(router['_id'], router['name'], router['online']))


@server.command()
@click.pass_context
@click.argument('token')
def claim(ctx, token):
    """
    Claim an existing router.
    """
    url = ctx.obj['routers_url'] + '/claim'
    data = {
        'claim_token': token
    }
    result = pdserver_request('POST', url, json=data)
    if result.ok:
        router = result.json()
        print("Claimed router: {}".format(router['name']))
    else:
        print("There was an error claiming the router.")
        print("Please check that your claim token is correct.")


@server.command()
@click.pass_context
@click.argument('name')
@click.option('--orphaned/--not-orphaned', default=False)
@click.option('--claim', default=None)
def create_router(ctx, name, orphaned, claim):
    """
    Create a new router.
    """
    url = ctx.obj['routers_url']
    data = {
        'name': name,
        'orphaned': orphaned
    }
    if claim is not None:
        data['claim_token'] = claim
    pdserver_request('POST', url, json=data)


@server.command()
@click.pass_context
@click.argument('router_id')
def delete_router(ctx, router_id):
    """
    Delete a router.
    """
    url = ctx.obj['routers_url'] + "/" + router_id
    pdserver_request('DELETE', url)
