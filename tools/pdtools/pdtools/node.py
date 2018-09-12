"""
This module defines click commands for managing a Paradrop edge compute
node.

One important point about how these commands are implemented is that
the target node is an optional argument. If the target is not specified,
it defaults to the local machine, which means these commands can be run
conveniently on a Paradrop node. It is also possible to override the
default target by setting the PDTOOLS_NODE_TARGET environment variable.
"""
import datetime
import getpass
import json
import operator
import os
import re
import tarfile
import tempfile
from six.moves.urllib.parse import urlparse

import arrow
import builtins
import click
import yaml

from . import util
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


def print_pdconf(data):
    data.sort(key=operator.itemgetter("age"))

    print("{:3s} {:12s} {:20s} {:30s} {:5s}".format("Age", "Type", "Name",
        "Comment", "Pass"))
    for item in data:
        print("{age:<3d} {type:12s} {name:20s} {comment:30s} {success}".format(**item))


@click.group('node')
@click.option('--target', '-t', default="172.17.0.1",
        help='Target node name or address')
@click.pass_context
def root(ctx, target):
    """
    Manage a Paradrop edge compute node.

    These commands respect the following environment variables:

    PDTOOLS_NODE_TARGET            Default target node name or address.
    """
    ctx.obj['target'] = target


@root.command('connect-snap-interfaces')
@click.pass_context
def connect_snap_interfaces(ctx):
    """
    Connect all interfaces for installed snaps.
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
    Create local Linux user connected to Ubuntu store account.

    EMAIL must be an email address which is registered as Ubuntu One
    account.  The name of the local account that is created will depend
    on the email address used. If in doubt, use "info@paradrop.io",
    which will result in a user named "paradrop" being created.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.create_user(email)
    click.echo(util.format_result(result))
    return result


@root.command('describe-audio')
@click.pass_context
def describe_audio(ctx):
    """
    Display audio subsystem information.

    Display information from the local PulseAudio server such as the
    default source and sink.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_audio()
    click.echo(util.format_result(result))
    return result


@root.command('describe-chute')
@click.argument('chute')
@click.pass_context
def describe_chute(ctx, chute):
    """
    Display information about a chute.

    CHUTE must be the name of an installed chute.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_chute(chute)
    click.echo(util.format_result(result))
    return result


@root.command('describe-chute-cache')
@click.argument('chute')
@click.pass_context
def describe_chute_cache(ctx, chute):
    """
    Show internal details from a chute installation.

    CHUTE must be the name of an installed chute.

    This information is intended for Paradrop daemon developers for
    debugging purposes. The output is not expected to remain stable
    between Paradrop versions.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_chute_cache(chute)
    click.echo(util.format_result(result))
    return result


@root.command('describe-chute-configuration')
@click.argument('chute')
@click.pass_context
def describe_chute_configuration(ctx, chute):
    """
    Display configuration of a chute.

    CHUTE must be the name of an installed chute.

    This information corresponds to the "config" section in a chute's
    paradrop.yaml file.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_chute_config(chute)
    click.echo(util.format_result(result))
    return result


@root.command('describe-chute-network-client')
@click.argument('chute')
@click.argument('network')
@click.argument('client')
@click.pass_context
def describe_chute_network_client(ctx, chute, network, client):
    """
    Display information about a network client.

    CHUTE must be the name of an installed chute.  NETWORK must be the
    name of one of the chute's configured networks. Typically, this
    will be "wifi".  CLIENT identifies the network client, such as a
    MAC address.
    """
    pdclient = ParadropClient(ctx.obj['target'])
    result = pdclient.get_chute_client(chute, network, client)
    click.echo(util.format_result(result))
    return result


@root.command('describe-pdconf')
@click.pass_context
def describe_pdconf(ctx):
    """
    Show status of the pdconf subsystem.

    This information is intended for Paradrop daemon developers for
    debugging purposes.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_pdconf()
    print_pdconf(result)
    return result


@root.command('describe-provision')
@click.pass_context
def describe_provision(ctx):
    """
    Show provisioning status of the node.

    This shows whether the node is associated with a cloud controller,
    and if so, its identifier.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_provision()
    click.echo(util.format_result(result))
    return result


@root.command('describe-settings')
@click.pass_context
def describe_settings(ctx):
    """
    Show node settings.

    These are settings that paradrop reads during startup and configure
    certain behaviors. They can only be modified through environment
    variables or the settings.ini file.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_settings()
    click.echo(util.format_result(result))
    return result


@root.command('edit-configuration')
@click.pass_context
def edit_configuration(ctx):
    """
    Interactively edit the node configuration and apply changes.

    Open the text editor specified by the EDITOR environment variable
    with the current node configuration. If you save and exit, the new
    configuration will be applied to the node.
    """
    client = ParadropClient(ctx.obj['target'])
    old_data = client.get_config()
    new_data, changed = util.open_yaml_editor(old_data, "node")
    if changed:
        result = client.set_config(new_data)
        ctx.invoke(watch_change_logs, change_id=result['change_id'])
    return new_data


@root.command('edit-chute-configuration')
@click.argument('chute')
@click.pass_context
def edit_chute_configuration(ctx, chute):
    """
    Interactively edit the chute configuration and restart it.

    CHUTE must be the name of an installed chute.

    Open the text editor specified by the EDITOR environment variable
    with the current chute configuration. If you save and exit, the new
    configuration will be applied and the chute restarted.
    """
    client = ParadropClient(ctx.obj['target'])
    old_data = client.get_chute_config(chute)
    new_data, changed = util.open_yaml_editor(old_data, "chute " + chute)
    if changed:
        result = client.set_chute_config(chute, new_data)
        ctx.invoke(watch_change_logs, change_id=result['change_id'])
    return new_data


@root.command('edit-chute-variables')
@click.argument('chute')
@click.pass_context
def edit_chute_variables(ctx, chute):
    """
    Interactively edit a chute's environment variables and restart it.

    CHUTE must be the name of an installed chute.

    Open the text editor specified by the EDITOR environment variable
    with the current chute environment variables. If you save and exit,
    the new settings will be applied and the chute restarted.
    """
    client = ParadropClient(ctx.obj['target'])
    old_data = client.get_chute(chute).get('environment', {})
    new_data, changed = util.open_yaml_editor(old_data, "chute " + chute)
    if changed:
        result = client.set_chute_variables(chute, new_data)
        ctx.invoke(watch_change_logs, change_id=result['change_id'])
    return new_data


@root.command('export-configuration')
@click.option('--format', '-f', default='json',
        help="Format (json or yaml)")
@click.pass_context
def export_configuration(ctx, format):
    """
    Display the node configuration in the desired format.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.get_config()

    format = format.lower()
    if format == 'json':
        click.echo(json.dumps(result, indent=4))
    elif format == 'yaml':
        click.echo(yaml.safe_dump(result, default_flow_style=False))
    else:
        click.echo("Unrecognized format: {}".format(format))
    return result


@root.command('generate-configuration')
@click.option('--format', '-f', default='json',
        help="Format (json or yaml)")
@click.pass_context
def generate_configuration(ctx, format):
    """
    Generate a new node configuration based on detected hardware.

    The new configuration is not automatically applied.  Rather, you can
    save it to file and use the import-configuration command to apply it.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.generate_config()

    format = format.lower()
    if format == 'json':
        click.echo(json.dumps(result, indent=4))
    elif format == 'yaml':
        click.echo(yaml.safe_dump(result, default_flow_style=False))
    else:
        click.echo("Unrecognized format: {}".format(format))
    return result


@root.command('help')
@click.pass_context
def help(ctx):
    """
    Show this message and exit.
    """
    click.echo(ctx.parent.get_help())


@root.command('import-configuration')
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def import_configuration(ctx, path):
    """
    Import a node configuration from file and apply changes.

    PATH must be a path to a node configuration file in YAML format.
    """
    with open(path, 'r') as source:
        config = yaml.safe_load(source)

    client = ParadropClient(ctx.obj['target'])
    result = client.set_config(config)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])
    return result


@root.command('import-ssh-key')
@click.argument('path', type=click.Path(exists=True))
@click.option('--user', '-u', default='paradrop', help='Local username')
@click.pass_context
def import_ssh_key(ctx, path, user):
    """
    Add an authorized key from a public key file.

    PATH must be a path to a public key file, which corresponds to
    a private key that SSH can use for authentication. Typically,
    ssh-keygen will place the public key in "~/.ssh/id_rsa.pub".
    """
    client = ParadropClient(ctx.obj['target'])
    with open(path, 'r') as source:
        key_string = source.read().strip()

    match = re.search("-----BEGIN \w+ PRIVATE KEY-----", key_string)
    if match is not None:
        print("The path ({}) contains a private key.".format(path))
        print("Please provide the path to your public key.")
        return None

    result = client.add_ssh_key(key_string, user=user)
    if result is not None:
        print("Added public key from {}".format(path))

    return result

@root.command('install-chute')
@click.option('--directory', '-d', default='.', help='Directory containing chute files')
@click.pass_context
def install_chute(ctx, directory):
    """
    Install a chute from the working directory.

    Install the files in the current directory as a chute on the node.
    The directory must contain a paradrop.yaml file.  The entire directory
    will be copied to the node for installation.
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
    List modules loaded by the audio subsystem.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_audio_modules()
    click.echo(util.format_result(result))
    return result


@root.command('list-audio-sinks')
@click.pass_context
def list_audio_sinks(ctx):
    """
    List audio sinks.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_audio_sinks()
    click.echo(util.format_result(result))
    return result


@root.command('list-audio-sources')
@click.pass_context
def list_audio_sources(ctx):
    """
    List audio sources.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_audio_sources()
    click.echo(util.format_result(result))
    return result


@root.command('list-changes')
@click.pass_context
def list_changes(ctx):
    """
    List queued or in progress changes.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_changes()
    click.echo(util.format_result(result))
    return result


@root.command('list-chute-networks')
@click.argument('chute')
@click.pass_context
def list_chute_networks(ctx, chute):
    """
    List networks configured by a chute.

    CHUTE must be the name of an installed chute.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_chute_networks(chute)
    click.echo(util.format_result(result))
    return result


@root.command('list-chute-network-clients')
@click.argument('chute')
@click.argument('network')
@click.pass_context
def list_chute_network_clients(ctx, chute, network):
    """
    List clients connected to the chute's network.

    CHUTE must be the name of an installed chute. NETWORK must be the
    name of one of its configured networks. Typically, this will be called
    "wifi".
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_chute_clients(chute, network)
    click.echo(util.format_result(result))
    return result


@root.command('list-chutes')
@click.pass_context
def list_chutes(ctx):
    """
    List chutes installed on the node
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_chutes()
    click.echo(util.format_result(result))
    return result


@root.command('list-devices')
@click.pass_context
def list_devices(ctx):
    """
    List devices connected to the node.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_devices()
    click.echo(util.format_result(result))
    return result


@root.command('list-snap-interfaces')
@click.pass_context
def list_snap_interfaces(ctx):
    """
    List interfaces for snaps installed on the node.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_snap_interfaces()
    click.echo(util.format_result(result))
    return result


@root.command('list-ssh-keys')
@click.option('--user', '-u', default='paradrop', help='Local username')
@click.pass_context
def list_ssh_keys(ctx, user):
    """
    List keys authorized for SSH access to the node.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.list_ssh_keys(user=user)
    click.echo(util.format_result(result))
    return result


@root.command('load-audio-module')
@click.argument('module')
@click.pass_context
def load_audio_module(ctx, module):
    """
    Load a module into the audio subsystem.

    MODULE must be the name of a PulseAudio module such as
    "module-loopback".
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.load_audio_module(module)
    click.echo(util.format_result(result))
    return result


@root.command('login')
@click.pass_context
def login(ctx):
    """
    Interactively log in using the local admin password.

    Authenticate with the node using the local username and
    password. Typically, the username will be "paradrop". The password
    can be set with the set-password command.
    """
    client = ParadropClient(ctx.obj['target'])
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
    client = ParadropClient(ctx.obj['target'])
    removed = client.logout()
    click.echo("Removed {} token(s).".format(removed))
    return removed


@root.command('open-chute-shell')
@click.argument('chute')
@click.option('--service', '-s', default="main", help="Service belonging to the chute")
@click.pass_context
def open_chute_shell(ctx, chute, service):
    """
    Open a shell inside the running chute.

    CHUTE must be the name of a running chute.

    This requires you to have enabled SSH access to the device and
    installed bash inside your chute.

    Changes made to files inside the chute may not be persistent if the
    chute or the node is restarted. Only changes to files in the "/data"
    directory will be preserved.
    """
    container_name = "{}-{}".format(chute, service)
    cmd = ["ssh", "-t", "paradrop@{}".format(ctx.obj['target']), "sudo", "docker",
            "exec", "-it", container_name, "/bin/bash"]
    os.spawnvpe(os.P_WAIT, "ssh", cmd, os.environ)


@root.command('provision')
@click.argument('id')
@click.argument('key')
@click.option('--controller', '-c', default="https://paradrop.org", help="Cloud controller endpoint")
@click.option('--wamp', '-w', default="ws://paradrop.org:9086/ws", help="WAMP endpoint")
@click.pass_context
def provision(ctx, id, key, controller, wamp):
    """
    Associate the node with a cloud controller.

    ID and KEY are credentials that can be found when creating a node
    on the controller, either through the website or through `pdtools
    cloud create-node`.  They may also be referred to as the Router ID
    and the Router Password.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.provision(id, key, controller=controller, wamp=wamp)
    click.echo(util.format_result(result))
    return result


@root.command('reboot')
@click.pass_context
def reboot(ctx):
    """
    Reboot the node.
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
    Remove a chute from the node.

    CHUTE must be the name of an installed chute.
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
    Remove a connected client from the chute's network.

    CHUTE must be the name of an installed chute.  NETWORK must be the
    name of one of the chute's configured networks. Typically, this
    will be "wifi".  CLIENT identifies the network client, such as a
    MAC address.

    Only implemented for wireless clients, this effectively kicks the
    client off the network.
    """
    pdclient = ParadropClient(ctx.obj['target'])
    result = pdclient.remove_chute_client(chute, network, client)
    click.echo(util.format_result(result))
    return result


@root.command('restart-chute')
@click.argument('chute')
@click.pass_context
def restart_chute(ctx, chute):
    """
    Restart a chute.

    CHUTE must be the name of an installed chute.
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
    Change a node configuration value and apply.

    PATH must be a dot-separated path to a value in the node
    configuration, such as "system.onMissingWiFi". VALUE will be
    interpreted as a string, numeric, or boolean type as appropriate.

    Changing values inside a list is not currently supported.
    Use edit-configuration instead.
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
    Configure audio sink volume.

    SINK must be the name of a PulseAudio sink. VOLUME should be one
    (applied to all channels) or multiple (one for each channel) floating
    point values between 0 and 1.
    """
    client = ParadropClient(ctx.obj['target'])

    # Convert to a list of floats. Be aware: the obvious approach
    # list(volume) behaves strangely.
    data = [float(vol) for vol in volume]

    result = client.set_sink_volume(sink, data)
    click.echo(util.format_result(result))
    return result


@root.command('set-source-volume')
@click.argument('source')
@click.argument('volume', nargs=-1)
@click.pass_context
def set_source_volume(ctx, source, volume):
    """
    Configure audio source volume.

    SOURCE must be the name of a PulseAudio source. VOLUME should be one
    (applied to all channels) or multiple (one for each channel) floating
    point values between 0 and 1.
    """
    client = ParadropClient(ctx.obj['target'])

    # Convert to a list of floats. Be aware: the obvious approach
    # list(volume) behaves strangely.
    data = [float(vol) for vol in volume]

    result = client.set_source_volume(source, data)
    click.echo(util.format_result(result))
    return result


@root.command('set-password')
@click.pass_context
def set_password(ctx):
    """
    Change the local admin password.

    Set the password required by `pdtools node login` and the local
    web-based administration page.
    """
    username = builtins.input("Username: ")
    while True:
        password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password == confirm:
            break
        else:
            print("Passwords do not match.")

    click.echo("Next, if prompted, you should enter the current username and password.")
    client = ParadropClient(ctx.obj['target'])
    result = client.set_password(username, password)
    click.echo(util.format_result(result))
    return result


@root.command('shutdown')
@click.pass_context
def shutdown(ctx):
    """
    Shut down the node.
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
    Start a stopped chute.

    CHUTE must be the name of a stopped chute.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.start_chute(chute)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('stop-chute')
@click.argument('chute')
@click.pass_context
def stop_chute(ctx, chute):
    """
    Stop a running chute.

    CHUTE must be the name of a running chute.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.stop_chute(chute)
    ctx.invoke(watch_change_logs, change_id=result['change_id'])


@root.command('trigger-pdconf')
@click.pass_context
def trigger_pdconf(ctx):
    """
    Trigger pdconf to reload configuration.

    This function is intended for Paradrop daemon developers for
    debugging purposes. Generally, you should use edit-configuration
    and edit-chute-configuration for making configuration changes.
    """
    client = ParadropClient(ctx.obj['target'])
    result = client.trigger_pdconf()
    print_pdconf(result)


@root.command('update-chute')
@click.option('--directory', '-d', default='.', help='Directory containing chute files')
@click.pass_context
def update_chute(ctx, directory):
    """
    Install a new version of the chute from the working directory.

    Install the files in the current directory as a chute on the node.
    The directory must contain a paradrop.yaml file.  The entire directory
    will be copied to the node for installation.
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
    Stream log messages from an in-progress change.

    CHANGE_ID must be the ID of a queued or in-progress change as
    retrieved from the list-changes command.
    """
    url = "ws://{}/ws/changes/{}/stream".format(ctx.obj['target'], change_id)

    def on_message(ws, message):
        data = json.loads(message)
        time = datetime.datetime.fromtimestamp(data['time'])
        msg = data['message'].rstrip()
        print("{}: {}".format(time, msg))

    client = ParadropClient(ctx.obj['target'])
    client.ws_request(url, on_message=on_message)


@root.command('watch-chute-logs')
@click.argument('chute')
@click.pass_context
def watch_chute_logs(ctx, chute):
    """
    Stream log messages from a running chute.

    CHUTE must be the name of a running chute.
    """
    url = "ws://{}/sockjs/logs/{}/websocket".format(ctx.obj['target'], chute)

    def on_message(ws, message):
        data = json.loads(message)
        time = arrow.get(data['timestamp']).to('local').datetime
        msg = data['message'].rstrip()
        service = data.get("service", chute)
        click.echo("[{}] {}: {}".format(service, time, msg))

    client = ParadropClient(ctx.obj['target'])
    client.ws_request(url, on_message=on_message)


@root.command('watch-logs')
@click.pass_context
def watch_logs(ctx):
    """
    Stream log messages from the Paradrop daemon.
    """
    url = "ws://{}/ws/paradrop_logs".format(ctx.obj['target'])

    def on_message(ws, message):
        print(message)

    client = ParadropClient(ctx.obj['target'])
    client.ws_request(url, on_message=on_message)
