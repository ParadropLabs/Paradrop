import builtins
import click
import git
import operator
import os
import yaml
from pprint import pprint

from .comm import pdserver_request


def chute_find_field(chute, key, default=Exception):
    """
    Find a field in a chute definition loading from a paradrop.yaml file.
    """
    if key in chute:
        return chute[key]
    elif 'config' in chute and key in chute['config']:
        return chute['config'][key]
    elif isinstance(default, type):
        raise default("{} field not found in chute definition.".format(key))
    else:
        return default


def chute_resolve_source(source, config):
    """
    Resolve the source section from paradrop.yaml to store configuration.

    If git/http, add an appropriate download section to the chute
    configuration. For git repos, we also identify the latest commit and add
    that to the download information. If type is inline, add a dockerfile
    string field to the chute and no download section.
    """
    if 'type' not in source:
        raise Exception("Source type not specified for chute.")

    source_type = source['type']
    if source_type == 'http':
        config['download'] = {
            'url': source['url']
        }

    elif source_type == 'git':
        repo = git.Repo('.')
        config['download'] = {
            'url': source['url'],
            'checkout': str(repo.head.commit)
        }

    elif source_type == 'inline':
        with open('Dockerfile', 'r') as dockerfile:
            config['dockerfile'] = dockerfile.read()

    else:
        raise Exception("Invalid source type {}".format(source_type))


@click.group()
@click.pass_context
def store(ctx):
    """
    Interact with chute store.
    """
    ctx.obj['chutes_url'] = ctx.obj['pdserver_url'] + '/api/chutes'


@store.command('create-version')
@click.pass_context
def create_version(ctx):
    """
    Push a new version to the chute store.
    """
    if not os.path.exists("paradrop.yaml"):
        raise Exception("No paradrop.yaml file found in working directory.")

    with open('paradrop.yaml', 'r') as source:
        chute = yaml.safe_load(source)

    name = chute_find_field(chute, 'name')
    source = chute_find_field(chute, 'source')
    config = chute.get('config', {})
    chute_id = None

    chute_resolve_source(source, config)

    result = pdserver_request('GET', ctx.obj['chutes_url'])
    if result.ok:
        data = result.json()
        for chute in data:
            if chute['name'] == name:
                chute_id = chute['_id']
                break

    if chute_id is None:
        raise Exception("Could not find ID for chute {} - is it registered?".format(name))

    data = {
        'chute_id': chute_id,
        'config': config
    }
    url = "{}/{}/versions".format(ctx.obj['chutes_url'], chute_id)
    result = pdserver_request('POST', url, data)
    if result.status_code == 201:
        response = result.json()
        print("Version {} created.".format(response['version']))


@store.command()
@click.pass_context
def list(ctx):
    """
    List chutes owned by the developer.
    """
    url = ctx.obj['chutes_url']

    result = pdserver_request('GET', url)
    if result.ok:
        data = result.json()

        print("Name                 Version Public")
        for chute in sorted(data, key=operator.itemgetter('name')):
            print("{name:20s} {current_version:7d} {public}".format(**chute))


@store.command()
@click.pass_context
@click.option('--public/--not-public', default=False)
def register(ctx, public):
    """
    Register a chute with the store.
    """
    url = ctx.obj['chutes_url']

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
        data = {
            'name': name,
            'description': description,
            'public': public
        }
        result = pdserver_request('POST', url, data)
        if result.status_code == 201:
            print("Chute created.")
        else:
            print("There was a problem creating the chute.")
            print("Perhaps the name is invalid or already in use.")
    else:
        print("Operation cancelled.")
