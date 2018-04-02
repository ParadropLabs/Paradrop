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

from .comm import change_json, router_login, router_logout, router_request, router_ws_request
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


def open_editor(data, description):
    if data is None:
        data = {}

    fd, path = tempfile.mkstemp()
    os.close(fd)

    with open(path, 'w') as output:
        if len(data) > 0:
            output.write(yaml.safe_dump(data, default_flow_style=False))
        output.write("\n")
        output.write("# You are editing the configuration for the {}.\n".format(description))
        output.write("# Blank lines and lines starting with '#' will be ignored.\n")
        output.write("# Save and exit to apply changes; exit without saving to discard.\n")

    # Get modified time before calling editor.
    orig_mtime = os.path.getmtime(path)

    editor = os.environ.get("EDITOR", "vim")
    os.spawnvpe(os.P_WAIT, editor, [editor, path], os.environ)

    with open(path, 'r') as source:
        data = source.read()
        new_data = yaml.safe_load(data)

    # If result is null, convert to an empty dict before sending to router.
    if new_data is None:
        new_data = {}

    # Check if the file has been modified, and if it has, send the update.
    new_mtime = os.path.getmtime(path)
    if new_mtime == orig_mtime:
        new_data = None

    os.remove(path)
    return new_data


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
    ctx.obj['target'] = target


@root.command('connect-snap-interfaces')
@click.pass_context
def connect_snap_interfaces(ctx):
    """
    Connect all interfaces for installed snaps
    """
    pass


@root.command('create-user')
@click.pass_context
def create_user(ctx, target):
    """
    Create local Linux user connected to Ubuntu store account
    """
    pass


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
    new_data = open_editor(old_data, "node")
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
    new_data = open_editor(old_data, "chute " + chute)
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
    new_data = open_editor(old_data, "chute " + chute)
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
@click.pass_context
def generate_configuration(ctx, target):
    """
    Generate a new node configuration and print or save to file
    """
    pass


@root.command('help')
@click.pass_context
def help(ctx):
    """
    Show this message and exit
    """
    click.echo(ctx.parent.get_help())


@root.command('import-configuration')
@click.pass_context
def import_configuration(ctx, target):
    """
    Import a node configuration from file and apply changes
    """
    pass


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
@click.pass_context
def install_chute(ctx, target):
    """
    Install a new chute from the working directory
    """
    pass


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
    click.echo('target: ' + ctx.obj['target'])
    pass


@root.command('logout')
@click.pass_context
def logout(ctx, target):
    """
    Log out by removing stored credentials
    """
    pass


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
def reboot(ctx, target):
    """
    Reboot the node
    """
    pass


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
@click.pass_context
def set_configuration(ctx, target):
    """
    Change a node configuration value and apply
    """
    pass


@root.command('set-sink-volume')
@click.pass_context
def set_sink_volume(ctx, target):
    """
    Configure audio sink volume
    """
    pass


@root.command('set-source-volume')
@click.pass_context
def set_source_volume(ctx, target):
    """
    Configure audio source volume
    """
    pass


@root.command('set-password')
@click.pass_context
def set_password(ctx, target):
    """
    Change the local admin password
    """
    pass


@root.command('shutdown')
@click.pass_context
def shutdown(ctx, target):
    """
    Shutdown the node
    """
    pass


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
@click.pass_context
def update_chute(ctx, target):
    """
    Install a new version of the chute from the working directory
    """
    pass


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
