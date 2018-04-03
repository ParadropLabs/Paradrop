import datetime
import getpass
import json
import operator
import os
import re
import tarfile
import tempfile
from pprint import pprint
from six.moves.urllib.parse import urlparse

import arrow
import builtins
import click
import yaml

from . import util
from .comm import router_ws_request
from .paradrop_client import ParadropClient


# Default target for node commands. Unless the environment variable is set, we
# will default to "localhost", which means all of the node commands can be run
# conveniently on the node itself.
PDTOOLS_TARGET_NODE = os.environ.get("PDTOOLS_TARGET_NODE", "localhost")


def get_base_url(target):
    if target.startswith("http"):
        parts = urlparse(target)

        if parts.scheme != 'http':
            print("Warning: when specifying the Paradrop device address, "
                  "using a scheme ({}) other than http may result in errors."
                  .format(parts.scheme))

        if not parts.path:
            path = "/api/v1"
        else:
            print("Warning: when specifying the Paradrop device address, "
                  "using a path ({}) other than /api/v1 may result in errors."
                  .format(parts.scheme))
            path = parts.path

        return "{}://{}{}".format(parts.scheme, parts.netloc, path)

    else:
        return "http://{}/api/v1".format(target)


def print_pdconf(data):
    data.sort(key=operator.itemgetter("age"))

    print("{:3s} {:12s} {:20s} {:30s} {:5s}".format("Age", "Type", "Name",
        "Comment", "Pass"))
    for item in data:
        print("{age:<3d} {type:12s} {name:20s} {comment:30s} {success}".format(**item))


@click.group('node')
@click.option('--target', '-t', default=PDTOOLS_TARGET_NODE,
        help='Target node name or address (default: {}'.format(PDTOOLS_TARGET_NODE))
@click.pass_context
def root(ctx, target):
    """
    Manage a Paradrop edge compute node.
    """
    ctx.obj['target'] = target


@root.command('connect-snap-interfaces')
@click.pass_context
def connect_snap_interfaces(ctx):
    """
    Connect all interfaces for installed snaps
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_snap_interfaces()
    for item in result['result']['plugs']:
        connections = item.get('connections', [])
        if len(connections) > 0:
            continue

        if item['plug'] == 'docker':
            # The docker slot needs to be treated differently from core slots.
            slot = {'snap': 'docker'}
        elif item['plug'] == 'zerotier-control':
            # TODO: This connection is failing, but I am not sure why.
            slot = {'snap': 'zerotier-one', 'slot': 'zerotier-control'}
        else:
            # Most slots are provided by the core snap and specified this way.
            slot = {'slot': item['interface']}

        result = client.connect_snap_interface(slots=[slot], plugs=[{'snap':
            item['snap'], 'plug': item['plug']}])
        if result['type'] == 'error':
            print(result['result']['message'])


@root.command('create-user')
@click.argument('email')
@click.pass_context
def create_user(ctx, email):
    """
    Create local Linux user connected to Ubuntu store account
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.create_user(email)
    pprint(result)


@root.command('describe-audio')
@click.pass_context
def describe_audio(ctx):
    """
    Display audio subsystem information
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_audio()
    pprint(result)


@root.command('describe-chute')
@click.argument('chute')
@click.pass_context
def describe_chute(ctx, chute):
    """
    Display information about the installed chute
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_chute(chute)
    pprint(result)


@root.command('describe-chute-cache')
@click.argument('chute')
@click.pass_context
def describe_chute_cache(ctx, chute):
    """
    Show internal details from the chute installation
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_chute_cache(chute)
    pprint(result)


@root.command('describe-chute-configuration')
@click.argument('chute')
@click.pass_context
def describe_chute_configuration(ctx, chute):
    """
    Display configuration of installed chute
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_chute_config(chute)
    pprint(result)


@root.command('describe-chute-network-client')
@click.argument('chute')
@click.argument('network')
@click.argument('client')
@click.pass_context
def describe_chute_network_client(ctx, chute, network, client):
    """
    Display information about a connected client
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_chute_client(chute, network, client)
    pprint(result)


@root.command('describe-pdconf')
@click.pass_context
def describe_pdconf(ctx):
    """
    Show status of the pdconf subsystem
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_pdconf()
    print_pdconf(result)


@root.command('describe-provision')
@click.pass_context
def describe_provision(ctx):
    """
    Show provisioning status of the node
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_provision()
    pprint(result)


@root.command('edit-configuration')
@click.pass_context
def edit_configuration(ctx):
    """
    Interactively edit the node configuration and apply changes
    """
    client = ParadropClient(ctx.obj['target'])
    old_data = client.get_config()
    new_data = util.open_yaml_editor(old_data, "node")
    if new_data is not None:
        result = client.set_config(new_data)
        ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('edit-chute-configuration')
@click.argument('chute')
@click.pass_context
def edit_chute_configuration(ctx, chute):
    """
    Interactively edit the chute configuration and restart it
    """
    client = ParadropClient(ctx.obj['target'])
    old_data = client.get_chute_config(chute)
    new_data = util.open_yaml_editor(old_data, "chute " + chute)
    if new_data is not None:
        result = client.set_chute_config(chute, new_data)
        ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('edit-chute-variables')
@click.argument('chute')
@click.pass_context
def edit_chute_variables(ctx, chute):
    """
    Interactively edit a chute's environment variables and restart it
    """
    client = ParadropClient(ctx.obj['target'])
    old_data = client.get_chute(chute).get('environment', {})
    new_data = util.open_yaml_editor(old_data, "chute " + chute)
    if new_data is not None:
        result = client.set_chute_variables(chute, new_data)
        ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('export-configuration')
@click.option('--format', '-f', help='Output format (json, yaml)')
@click.pass_context
def export_configuration(ctx, format):
    """
    Retrieve the node configuration and print or save to file
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_config()
    if format == 'json':
        print(json.dumps(result, indent=4))
    elif format == 'yaml':
        print(yaml.safe_dump(result, default_flow_style=False))
    else:
        pprint(result)


@root.command('generate-configuration')
@click.option('--format', '-f', help='Output format (json, yaml)')
@click.pass_context
def generate_configuration(ctx, format):
    """
    Generate a new node configuration and print or save to file
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.generate_config()
    if format == 'json':
        print(json.dumps(result, indent=4))
    elif format == 'yaml':
        print(yaml.safe_dump(result, default_flow_style=False))
    else:
        pprint(result)


@root.command('help')
@click.pass_context
def help(ctx):
    """
    Show this message and exit
    """
    click.echo(ctx.parent.get_help())


@root.command('import-configuration')
@click.argument('path')
@click.pass_context
def import_configuration(ctx, path):
    """
    Import a node configuration from file and apply changes
    """
    with open(path, 'r') as source:
        config = yaml.safe_load(source)

    client = ParadropClient(ctx.obj['target'])
    result = client.set_config(config)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('import-ssh-key')
@click.argument('path')
@click.option('--user', '-u', default='paradrop', help='Local username')
@click.pass_context
def import_ssh_key(ctx, path, user):
    """
    Add an authorized key from a public key file
    """
    client = ParadropClient(ctx.obj['target'])
    with open(path, 'r') as source:
        key_string = source.read().strip()

    match = re.search("-----BEGIN \w+ PRIVATE KEY-----", key_string)
    if match is not None:
        print("The path ({}) contains a private key.".format(path))
        print("Please provide the path to your public key.")
        return

    result = client.add_ssh_key(key_string, user=user)
    pprint(result)


@root.command('install-chute')
@click.option('--directory', '-d', default='.', help='Directory containing chute files')
@click.pass_context
def install_chute(ctx, directory):
    """
    Install a new chute from the working directory
    """
    os.chdir(directory)

    if not os.path.exists("paradrop.yaml"):
        raise Exception("No paradrop.yaml file found in chute directory.")

    client = ParadropClient(ctx.obj['target'])
    with tempfile.TemporaryFile() as temp:
        tar = tarfile.open(fileobj=temp, mode="w")
        for dirName, subdirList, fileList in os.walk("."):
            for fname in fileList:
                path = os.path.join(dirName, fname)
                arcname = os.path.normpath(path)
                tar.add(path, arcname=arcname)
        tar.close()

        temp.seek(0)
        result = client.install_tar(temp)
        ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('list-audio-modules')
@click.pass_context
def list_audio_modules(ctx):
    """
    List modules loaded by the audio subsystem
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_audio_modules()
    pprint(result)


@root.command('list-audio-sinks')
@click.pass_context
def list_audio_sinks(ctx):
    """
    List audio sinks
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_audio_sinks()
    pprint(result)


@root.command('list-audio-sources')
@click.pass_context
def list_audio_sources(ctx):
    """
    List audio sources
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_audio_sources()
    pprint(result)


@root.command('list-changes')
@click.pass_context
def list_changes(ctx, target):
    """
    List queued or in progress changes
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_changes()
    pprint(result)


@root.command('list-chute-networks')
@click.argument('chute')
@click.pass_context
def list_chute_networks(ctx, chute):
    """
    List networks configured by a chute
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_chute_networks(chute)
    pprint(result)


@root.command('list-chute-network-clients')
@click.argument('chute')
@click.argument('network')
@click.pass_context
def list_chute_network_clients(ctx, chute, network):
    """
    List clients connected to the chute's network
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_chute_clients(chute, network)
    pprint(result)


@root.command('list-chutes')
@click.pass_context
def list_chutes(ctx):
    """
    List chutes installed on the node
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_chutes()
    pprint(result)


@root.command('list-snap-interfaces')
@click.pass_context
def list_snap_interfaces(ctx):
    """
    List interfaces for snaps installed on the node
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_snap_interfaces()
    pprint(result)


@root.command('list-ssh-keys')
@click.option('--user', '-u', default='paradrop', help='Local username')
@click.pass_context
def list_ssh_keys(ctx, user):
    """
    List authorized keys for SSH access
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_ssh_keys(user=user)
    pprint(result)


@root.command('load-audio-module')
@click.argument('module')
@click.pass_context
def load_audio_module(ctx, module):
    """
    Load a module into the audio subsystem
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.load_audio_module(module)
    pprint(result)


@root.command('login')
@click.pass_context
def login(ctx):
    """
    Interactively login using the local admin password
    """
    client = ParadropClient(ctx.obj['target'])
    token = client.login()
    if token is None:
        click.echo("Login attempt failed.")
    else:
        click.echo("Login successful.")


@root.command('logout')
@click.pass_context
def logout(ctx):
    """
    Log out by removing stored credentials
    """
    client = ParadropClient(ctx.obj['target'])
    removed = client.logout()
    click.echo("Removed {} token(s).".format(removed))


@root.command('open-chute-shell')
@click.argument('chute')
@click.pass_context
def open_chute_shell(ctx, chute):
    """
    Open a shell inside the running chute

    This requires you to have enabled SSH access to the device and installed
    bash inside your chute.
    """
    cmd = ["ssh", "-t", "paradrop@{}".format(ctx.obj['target']), "sudo", "docker",
            "exec", "-it", chute, "/bin/bash"]
    os.spawnvpe(os.P_WAIT, "ssh", cmd, os.environ)


@root.command('provision')
@click.argument('id')
@click.argument('key')
@click.option('--controller', '-c', default="https://paradrop.org", help="Cloud controller endpoint")
@click.option('--wamp', '-w', default="ws://paradrop.org:9086/ws", help="WAMP endpoint")
@click.pass_context
def provision(ctx, id, key, controller, wamp):
    """
    Associate the node with a cloud controller
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.provision(id, key, controller=controller, wamp=wamp)
    pprint(result)


@root.command('reboot')
@click.pass_context
def reboot(ctx):
    """
    Reboot the node
    """
    change = {
        'name': '__PARADROP__',
        'updateClass': 'ROUTER',
        'updateType': 'reboot'
    }
    client = ParadropClient(ctx.obj['target'])
    result = client.add_change(change)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('remove-chute')
@click.argument('chute')
@click.pass_context
def remove_chute(ctx, chute):
    """
    Remove a chute from the node
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.remove_chute(chute)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('remove-chute-network-client')
@click.argument('chute')
@click.argument('network')
@click.argument('client')
@click.pass_context
def remove_chute_network_client(ctx, chute, network, client):
    """
    Remove a connected client from the chute's network
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.remove_chute_client(chute, network, client)
    pprint(result)


@root.command('restart-chute')
@click.argument('chute')
@click.pass_context
def restart_chute(ctx, chute):
    """
    Restart a chute
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.restart_chute(chute)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('set-configuration')
@click.argument('path')
@click.argument('value')
@click.pass_context
def set_configuration(ctx, path, value):
    """
    Change a node configuration value and apply
    """
    client = ParadropClient(ctx.obj['target'])
    config = client.get_config()

    # This does some type inference for boolean, numerics, etc.
    value = yaml.safe_load(value)

    def set_value(parent, key, created):
        if created:
            print("Created new field {} = {}".format(path, value))
        else:
            current = parent[key]
            print("Changed {} from {} to {}".format(path, current, value))
        parent[key] = value

    util.update_object(config, path, set_value)

    result = client.set_config(config)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('set-sink-volume')
@click.argument('sink')
@click.argument('volume', nargs=-1)
@click.pass_context
def set_sink_volume(ctx, sink, volume):
    """
    Configure audio sink volume
    """
    client = ParadropClient(ctx.obj['target'])

    # Convert to a list of floats. Be aware: the obvious approach
    # list(volume) behaves strangely.
    data = [float(vol) for vol in volume]

    result = client.set_sink_volume(sink, data)
    pprint(result)


@root.command('set-source-volume')
@click.argument('source')
@click.argument('volume', nargs=-1)
@click.pass_context
def set_source_volume(ctx, source, volume):
    """
    Configure audio source volume
    """
    client = ParadropClient(ctx.obj['target'])

    # Convert to a list of floats. Be aware: the obvious approach
    # list(volume) behaves strangely.
    data = [float(vol) for vol in volume]

    result = client.set_source_volume(source, data)
    pprint(result)


@root.command('set-password')
@click.pass_context
def set_password(ctx):
    """
    Change the local admin password
    """
    username = builtins.input("Username: ")
    while True:
        password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password == confirm:
            break
        else:
            print("Passwords do not match.")

    print("Next, if prompted, you should enter the current username and password.")
    client = ParadropClient(ctx.obj['target'])
    result = client.set_password(username, password)
    pprint(result)


@root.command('shutdown')
@click.pass_context
def shutdown(ctx):
    """
    Shutdown the node
    """
    change = {
        'name': '__PARADROP__',
        'updateClass': 'ROUTER',
        'updateType': 'shutdown'
    }
    client = ParadropClient(ctx.obj['target'])
    result = client.add_change(change)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('start-chute')
@click.argument('chute')
@click.pass_context
def start_chute(ctx, chute):
    """
    Start a stopped chute
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.start_chute(chute)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('stop-chute')
@click.argument('chute')
@click.pass_context
def stop_chute(ctx, chute):
    """
    Stop a running chute
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.stop_chute(chute)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('trigger-pdconf')
@click.pass_context
def trigger_pdconf(ctx):
    """
    Trigger pdconf to reload configuration
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.trigger_pdconf()
    print_pdconf(result)


@root.command('update-chute')
@click.option('--directory', '-d', default='.', help='Directory containing chute files')
@click.pass_context
def update_chute(ctx, directory):
    """
    Install a new version of the chute from the working directory
    """
    os.chdir(directory)

    if not os.path.exists("paradrop.yaml"):
        raise Exception("No paradrop.yaml file found in chute directory.")

    with open('paradrop.yaml', 'r') as source:
        config = yaml.safe_load(source)

    if 'name' not in config:
        click.echo('Chute name is not defined in paradrop.yaml.')
        return

    client = ParadropClient(ctx.obj['target'])
    with tempfile.TemporaryFile() as temp:
        tar = tarfile.open(fileobj=temp, mode="w")
        for dirName, subdirList, fileList in os.walk("."):
            for fname in fileList:
                path = os.path.join(dirName, fname)
                arcname = os.path.normpath(path)
                tar.add(path, arcname=arcname)
        tar.close()

        temp.seek(0)
        result = client.install_tar(temp, name=config['name'])
        ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('watch-change-logs')
@click.argument('change_id')
@click.pass_context
def watch_change_logs(ctx, change_id):
    """
    Stream log messages from an in-progress change
    """
    url = "ws://{}/ws/changes/{}/stream".format(ctx.obj['target'], change_id)

    def on_message(ws, message):
        data = json.loads(message)
        time = datetime.datetime.fromtimestamp(data['time'])
        msg = data['message'].rstrip()
        print("{}: {}".format(time, msg))

    router_ws_request(url, on_message=on_message)


@root.command('watch-chute-logs')
@click.argument('chute')
@click.pass_context
def watch_chute_logs(ctx, chute):
    """
    Stream log messages from a running chute
    """
    url = "ws://{}/sockjs/logs/{}/websocket".format(ctx.obj['target'], chute)

    def on_message(ws, message):
        data = json.loads(message)
        time = arrow.get(data['timestamp']).to('local').datetime
        msg = data['message'].rstrip()
        print("{}: {}".format(time, msg))

    router_ws_request(url, on_message=on_message)


@root.command('watch-logs')
@click.pass_context
def watch_logs(ctx):
    """
    Stream log messages from the Paradrop daemon
    """
    url = "ws://{}/ws/paradrop_logs".format(ctx.obj['target'])

    def on_message(ws, message):
        print(message)

    router_ws_request(url, on_message=on_message)
