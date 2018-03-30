import datetime
import getpass
import json
import operator
import os
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


@click.group('node')
@click.option('--target', '-t', default='localhost', help='Target node name or address')
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
@click.pass_context
def describe_chute_network_client(ctx, target):
    """
    Display information about a connected client
    """
    pass


@root.command('describe-pdconf')
@click.pass_context
def describe_pdconf(ctx, target):
    """
    Show status of the pdconf subsystem
    """
    pass


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


@root.command('import-configuration')
@click.pass_context
def import_configuration(ctx, target):
    """
    Import a node configuration from file and apply changes
    """
    pass


@root.command('import-ssh-key')
@click.pass_context
def import_ssh_key(ctx, target):
    """
    Add an authorized key from a public key file
    """
    pass


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
@click.pass_context
def list_chute_network_clients(ctx, target):
    """
    List clients connected to the chute's network
    """
    pass


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
@click.pass_context
def list_ssh_keys(ctx, target):
    """
    List authorized keys for SSH access
    """
    pass


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
@click.pass_context
def provision(ctx, target):
    """
    Associate the node with a cloud controller
    """
    pass


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
@click.pass_context
def remove_chute_network_client(ctx):
    """
    Remove a connected client from the chute's network
    """
    pass


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
def trigger_pdconf(ctx, target):
    """
    Trigger pdconf to reload configuration
    """
    pass


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
@click.pass_context
def watch_chute_logs(ctx, target):
    """
    Stream log messages from a running chute
    """
    pass
