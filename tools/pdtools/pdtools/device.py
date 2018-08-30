import datetime
import getpass
import json
import operator
import os
import tarfile
import tempfile
from six.moves.urllib.parse import urlparse

import arrow
import builtins
import click
import yaml

from .comm import change_json, router_login, router_logout, router_request, router_ws_request


@click.group()
@click.argument('address')
@click.pass_context
def device(ctx, address):
    """
    (deprecated) Sub-tree for configuring a device.

    These commands are deprecated. Please use the equivalent commands under
    `pdtools node --help`.
    """
    if address.startswith("http"):
        parts = urlparse(address)
        ctx.obj['address'] = parts.netloc

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

        ctx.obj['base_url'] = "{}://{}{}".format(parts.scheme, parts.netloc, path)
        print(ctx.obj['base_url'])

    else:
        ctx.obj['address'] = address
        ctx.obj['base_url'] = "http://{}/api/v1".format(address)


@device.group()
@click.pass_context
def audio(ctx):
    """
    Control device audio properties.
    """
    url = "{}/audio".format(ctx.obj['base_url'])
    ctx.obj['audio_url'] = url


@audio.command()
@click.pass_context
def info(ctx):
    """
    Get audio server information.
    """
    url = "{}/info".format(ctx.obj['audio_url'])
    router_request("GET", url)


@audio.command()
@click.pass_context
def modules(ctx):
    """
    List loaded modules.
    """
    url = "{}/modules".format(ctx.obj['audio_url'])
    router_request("GET", url)


@audio.command('load-module')
@click.pass_context
@click.argument('name')
def load_module(ctx, name):
    """
    Load a module.
    """
    url = "{}/modules".format(ctx.obj['audio_url'])
    data = { 'name': name }
    router_request("POST", url, json=data)


@audio.command()
@click.pass_context
def sinks(ctx):
    """
    List audio sinks.
    """
    url = "{}/sinks".format(ctx.obj['audio_url'])
    router_request("GET", url)


@audio.group()
@click.pass_context
@click.argument('sink_name')
def sink(ctx, sink_name):
    """
    Configure audio sink.
    """
    url = "{}/sinks/{}".format(ctx.obj['audio_url'], sink_name)
    ctx.obj['sink_url'] = url


@sink.command('volume')
@click.pass_context
@click.argument('channel_volume', nargs=-1)
def sink_volume(ctx, channel_volume):
    """
    Set sink volume.
    """
    url = "{}/volume".format(ctx.obj['sink_url'])

    # Convert to a list of floats. Be aware: the obvious approach
    # list(channel_volume) behaves strangely.
    data = [float(vol) for vol in channel_volume]

    router_request("PUT", url, json=data)


@audio.command()
@click.pass_context
def sources(ctx):
    """
    List audio sources.
    """
    url = "{}/sources".format(ctx.obj['audio_url'])
    router_request("GET", url)


@audio.group()
@click.pass_context
@click.argument('source_name')
def source(ctx, source_name):
    """
    Configure audio source.
    """
    url = "{}/sources/{}".format(ctx.obj['audio_url'], source_name)
    ctx.obj['source_url'] = url


@source.command('volume')
@click.pass_context
@click.argument('channel_volume', nargs=-1)
def source_volume(ctx, channel_volume):
    """
    Set source volume.
    """
    url = "{}/volume".format(ctx.obj['source_url'])

    # Convert to a list of floats. Be aware: the obvious approach
    # list(channel_volume) behaves strangely.
    data = [float(vol) for vol in channel_volume]

    router_request("PUT", url, json=data)


@device.command()
@click.pass_context
def changes(ctx):
    """
    List changes in the working queue.
    """
    url = "{}/changes/".format(ctx.obj['base_url'])
    router_request("GET", url)


@device.command()
@click.pass_context
@click.argument('change_id')
def watch(ctx, change_id):
    """
    Stream messages for a change in progress.
    """
    url = "ws://{}/ws/changes/{}/stream".format(ctx.obj['address'], change_id)

    def on_message(ws, message):
        data = json.loads(message)
        time = datetime.datetime.fromtimestamp(data['time'])
        msg = data['message'].rstrip()
        print("{}: {}".format(time, msg))

    router_ws_request(url, on_message=on_message)


@device.group()
@click.pass_context
def chutes(ctx):
    """
    View or create chutes on the router.
    """
    pass


@chutes.command()
@click.pass_context
def list(ctx):
    """
    List chutes installed on the router.
    """
    url = "{}/chutes/".format(ctx.obj['base_url'])
    router_request("GET", url)


@chutes.command()
@click.pass_context
def create(ctx):
    """
    Install a chute from the working directory.
    """
    url = "{}/chutes/".format(ctx.obj['base_url'])
    headers = {'Content-Type': 'application/x-tar'}

    if not os.path.exists("paradrop.yaml"):
        raise Exception("No paradrop.yaml file found in working directory.")

    with tempfile.TemporaryFile() as temp:
        tar = tarfile.open(fileobj=temp, mode="w")
        for dirName, subdirList, fileList in os.walk('.'):
            for fname in fileList:
                path = os.path.join(dirName, fname)
                arcname = os.path.normpath(path)
                tar.add(path, arcname=arcname)
        tar.close()

        temp.seek(0)
        res = router_request("POST", url, headers=headers, data=temp)
        data = res.json()
        ctx.invoke(watch, change_id=data['change_id'])


@device.group()
@click.argument('chute')
@click.pass_context
def chute(ctx, chute):
    """
    Sub-tree for configuring a chute.
    """
    ctx.obj['chute'] = chute
    ctx.obj['chute_url'] = "{}/chutes/{}".format(ctx.obj['base_url'], chute)


@chute.command()
@click.pass_context
def start(ctx):
    """
    Start the chute.
    """
    url = ctx.obj['chute_url'] + "/start"
    res = router_request("POST", url)
    data = res.json()
    ctx.invoke(watch, change_id=data['change_id'])


@chute.command()
@click.pass_context
def stop(ctx):
    """
    Stop the chute.
    """
    url = ctx.obj['chute_url'] + "/stop"
    res = router_request("POST", url)
    data = res.json()
    ctx.invoke(watch, change_id=data['change_id'])


@chute.command()
@click.pass_context
def restart(ctx):
    """
    Restart the chute.
    """
    url = ctx.obj['chute_url'] + "/restart"
    res = router_request("POST", url)
    data = res.json()
    ctx.invoke(watch, change_id=data['change_id'])


@chute.command('edit-environment')
@click.pass_context
def edit_environment(ctx):
    """
    Interactively edit the chute environment vairables.
    """
    req = router_request("GET", ctx.obj['chute_url'], dump=False)
    info = req.json()
    old_environ = info.get('environment', None)
    if old_environ is None:
        old_environ = {}

    fd, path = tempfile.mkstemp()
    os.close(fd)

    with open(path, 'w') as output:
        if len(old_environ) > 0:
            output.write(yaml.safe_dump(old_environ, default_flow_style=False))
        output.write("\n")
        output.write("# You are editing the environment variables for the chute {}.\n"
                .format(ctx.obj['chute']))
        output.write("# Blank lines and lines starting with '#' will be ignored.\n")
        output.write("# Put each variable on a line with a colon separator, e.g. 'VARIABLE: VALUE'\n")
        output.write("# Save and exit to apply changes; exit without saving to discard.\n")

    # Get modified time before calling editor.
    orig_mtime = os.path.getmtime(path)

    editor = os.environ.get("EDITOR", "vim")
    os.spawnvpe(os.P_WAIT, editor, [editor, path], os.environ)

    with open(path, 'r') as source:
        data = source.read()
        new_environ = yaml.safe_load(data)

    # If result is null, convert to an empty dict before sending to router.
    if new_environ is None:
        new_environ = {}

    # Check if the file has been modified, and if it has, send the update.
    new_mtime = os.path.getmtime(path)
    if new_mtime != orig_mtime:
        data = {
            'environment': new_environ
        }
        url = ctx.obj['chute_url'] + "/restart"
        res = router_request("POST", url, json=data)
        data = res.json()
        ctx.invoke(watch, change_id=data['change_id'])

    os.remove(path)


@chute.command()
@click.pass_context
def delete(ctx):
    """
    Uninstall the chute.
    """
    url = ctx.obj['chute_url']
    res = router_request("DELETE", url)
    data = res.json()
    ctx.invoke(watch, change_id=data['change_id'])


@chute.command('info')
@click.pass_context
def chute_info(ctx):
    """
    Get information about the chute.
    """
    url = ctx.obj['chute_url']
    router_request("GET", url)


@chute.command()
@click.pass_context
def cache(ctx):
    """
    Get details from the chute installation.
    """
    url = ctx.obj['chute_url'] + "/cache"
    router_request("GET", url)


@chute.command()
@click.pass_context
def logs(ctx):
    """
    Watch log messages from a chute.
    """
    url = "ws://{}/sockjs/logs/{}/websocket".format(ctx.obj['address'], ctx.obj['chute'])

    def on_message(ws, message):
        data = json.loads(message)
        time = arrow.get(data['timestamp']).to('local').datetime
        msg = data['message'].rstrip()
        print("{}: {}".format(time, msg))

    router_ws_request(url, on_message=on_message)


@chute.command()
@click.pass_context
def update(ctx):
    """
    Update the chute from the working directory.
    """
    url = ctx.obj['chute_url']
    headers = {'Content-Type': 'application/x-tar'}

    if not os.path.exists("paradrop.yaml"):
        raise Exception("No paradrop.yaml file found in working directory.")

    with tempfile.TemporaryFile() as temp:
        tar = tarfile.open(fileobj=temp, mode="w")
        for dirName, subdirList, fileList in os.walk('.'):
            for fname in fileList:
                path = os.path.join(dirName, fname)
                arcname = os.path.normpath(path)
                tar.add(path, arcname=arcname)
        tar.close()

        temp.seek(0)
        res = router_request("PUT", url, headers=headers, data=temp)
        data = res.json()
        ctx.invoke(watch, change_id=data['change_id'])


@chute.command()
@click.pass_context
def config(ctx):
    """
    Get the chute's current configuration.
    """
    url = ctx.obj['chute_url'] + "/config"
    router_request("GET", url)


@chute.command()
@click.pass_context
def reconfigure(ctx):
    """
    Reconfigure the chute without rebuilding.
    """
    url = ctx.obj['chute_url'] + "/config"

    if not os.path.exists("paradrop.yaml"):
        raise Exception("No paradrop.yaml file found in working directory.")

    with open("paradrop.yaml", "r") as source:
        data = yaml.safe_load(source)
        config = data.get('config', {})

    res = router_request("PUT", url, json=config)
    data = res.json()
    ctx.invoke(watch, change_id=data['change_id'])


@chute.command()
@click.pass_context
def networks(ctx):
    """
    List the chute's networks.
    """
    url = ctx.obj['chute_url'] + "/networks"
    router_request("GET", url)


@chute.command()
@click.pass_context
def shell(ctx):
    """
    Open a shell inside a chute.

    This requires you to have enabled SSH access to the device and installed
    bash inside your chute.
    """
    cmd = ["ssh", "-t", "paradrop@{}".format(ctx.obj['address']), "sudo", "docker",
            "exec", "-it", ctx.obj['chute'], "/bin/bash"]
    os.spawnvpe(os.P_WAIT, "ssh", cmd, os.environ)


@chute.group()
@click.pass_context
@click.argument('network')
def network(ctx, network):
    """
    Sub-tree for accessing chute network.
    """
    ctx.obj['network'] = network
    ctx.obj['network_url'] = "{}/networks/{}".format(ctx.obj['chute_url'],
            network)


@network.command()
@click.pass_context
def stations(ctx):
    """
    List stations connected to the network.
    """
    url = ctx.obj['network_url'] + "/stations"
    router_request("GET", url)


@network.group()
@click.pass_context
@click.argument('station')
def station(ctx, station):
    """
    Sub-tree for accessing network stations.
    """
    ctx.obj['station'] = station
    ctx.obj['station_url'] = ctx.obj['network_url'] + "/stations/" + station


@station.command()
@click.pass_context
def show(ctx):
    """
    Show station information.
    """
    router_request("GET", ctx.obj['station_url'])


@station.command('delete')
@click.pass_context
def station_delete(ctx):
    """
    Kick a station off the network.
    """
    router_request("DELETE", ctx.obj['station_url'])


@device.group(invoke_without_command=True)
@click.pass_context
def hostconfig(ctx):
    """
    Sub-tree for the host configuration.
    """
    url = ctx.obj['base_url'] + "/config/hostconfig"
    router_request("GET", url)


@device.command()
@click.pass_context
def login(ctx):
    """
    Log in using device-local credentials.
    """
    username = router_login(ctx.obj['base_url'])
    if username is not None:
        print("Logged in as: {}".format(username))
    else:
        print("Log in failed.")


@device.command()
@click.pass_context
def logout(ctx):
    """
    Log out by removing any stored access tokens.
    """
    removed = router_logout(ctx.obj['base_url'])
    print("Removed {} token(s).".format(removed))


@hostconfig.command()
@click.pass_context
@click.argument('option')
@click.argument('value')
def change(ctx, option, value):
    """
    Change one setting in the host configuration.
    """
    url = ctx.obj['base_url'] + "/config/hostconfig"
    req = router_request("GET", url, dump=False)
    config = req.json()

    change_json(config, option, value)
    data = {
        'config': config
    }
    router_request("PUT", url, json=data)


@hostconfig.command()
@click.pass_context
def edit(ctx):
    """
    Interactively edit the host configuration.
    """
    url = ctx.obj['base_url'] + "/config/hostconfig"
    req = router_request("GET", url, dump=False)
    config = req.json()

    fd, path = tempfile.mkstemp()
    os.close(fd)

    with open(path, 'w') as output:
        output.write(yaml.safe_dump(config, default_flow_style=False))

    # Get modified time before calling editor.
    orig_mtime = os.path.getmtime(path)

    editor = os.environ.get("EDITOR", "vim")
    os.spawnvpe(os.P_WAIT, editor, [editor, path], os.environ)

    with open(path, 'r') as source:
        data = source.read()
        config = yaml.safe_load(data)

    # Check if the file has been modified, and if it has, send the update.
    new_mtime = os.path.getmtime(path)
    if new_mtime != orig_mtime:
        data = {
            'config': config
        }
        res = router_request("PUT", url, json=data)
        result = res.json()
        ctx.invoke(watch, change_id=result['change_id'])

    os.remove(path)


@device.group()
@click.pass_context
@click.option('--user', default='paradrop')
def sshkeys(ctx, user):
    """
    Sub-tree for accessing SSH authorized keys.
    """
    ctx.obj['sshkeys_user'] = user
    ctx.obj['sshkeys_url'] = ctx.obj['base_url'] + '/config/sshKeys'


@sshkeys.command()
@click.pass_context
@click.argument('path')
def add(ctx, path):
    """
    Add an authorized key from a file.
    """
    url = '{sshkeys_url}/{sshkeys_user}'.format(**ctx.obj)
    with open(path, 'r') as source:
        key_string = source.read().strip()
        data = {
            'key': key_string
        }

        result = router_request("POST", url, json=data, dump=False)
        if result.ok:
            data = result.json()
            print("Added: " + data.get('key', ''))


@sshkeys.command('list')
@click.pass_context
def sshkeys_list(ctx):
    """
    List authorized keys.
    """
    url = '{sshkeys_url}/{sshkeys_user}'.format(**ctx.obj)
    result = router_request("GET", url, dump=False)
    if result.ok:
        keys = result.json()
        for key in keys:
            print(key)


@device.command()
@click.pass_context
def password(ctx):
    """
    Change the router admin password.
    """
    url = ctx.obj['base_url'] + "/password/change"

    username = builtins.input("Username: ")
    while True:
        password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password == confirm:
            break
        else:
            print("Passwords do not match.")

    data = {
        "username": username,
        "password": password
    }
    router_request("POST", url, json=data)


@device.command()
@click.pass_context
@click.argument('router_id')
@click.argument('router_password')
@click.option('--server', default="https://paradrop.org")
@click.option('--wamp', default="ws://paradrop.org:9086/ws")
def provision(ctx, router_id, router_password, server, wamp):
    """
    Provision the router.
    """
    url = ctx.obj['base_url'] + "/config/provision"

    data = {
        'routerId': router_id,
        'apitoken': router_password,
        'pdserver': server,
        'wampRouter': wamp
    }
    router_request("POST", url, json=data)


def print_pdconf(res):
    if res.ok:
        data = res.json()
        data.sort(key=operator.itemgetter("age"))

        print("{:3s} {:12s} {:20s} {:30s} {:5s}".format("Age", "Type", "Name",
            "Comment", "Pass"))
        for item in data:
            print("{age:<3d} {type:12s} {name:20s} {comment:30s} {success}".format(**item))


@device.group()
@click.pass_context
def pdconf(ctx):
    """
    Access the pdconf subsystem.

    pdconf manages low-level configuration of the Paradrop device.
    These commands are implemented for debugging purposes and are
    not intended for ordinary configuration purposes.
    """
    pass


@pdconf.command('show')
@click.pass_context
def pdconf_show(ctx):
    """
    Show status of pdconf subsystem.
    """
    url = ctx.obj['base_url'] + "/config/pdconf"
    res = router_request("GET", url, dump=False)
    print_pdconf(res)


@pdconf.command()
@click.pass_context
def reload(ctx):
    """
    Force pdconf to reload files.
    """
    url = ctx.obj['base_url'] + "/config/pdconf"
    res = router_request("PUT", url, dump=False)
    print_pdconf(res)


@device.group()
@click.pass_context
def snapd(ctx):
    """
    Access the snapd subsystem.
    """
    ctx.obj['snapd_url'] = "http://{}/snapd".format(ctx.obj['address'])


@snapd.command()
@click.pass_context
@click.argument('email')
def createUser(ctx, email):
    """
    Create user account.
    """
    url = ctx.obj['snapd_url'] + "/v2/create-user"
    data = {
        'email': email,
        'sudoer': True
    }
    router_request("POST", url, json=data)


@snapd.command()
@click.pass_context
def connectAll(ctx):
    """
    Connect all interfaces.
    """
    url = ctx.obj['snapd_url'] + "/v2/interfaces"
    res = router_request("GET", url, dump=False)
    data = res.json()
    for item in data['result']['plugs']:
        connections = item.get('connections', [])
        if len(connections) > 0:
            continue

        if item['plug'] == 'docker':
            # The docker slot needs to be treated differently from core slots.
            slot = {'snap': 'docker'}
        elif item['plug'] == 'zerotier-control':
            slot = {'snap': 'zerotier-one'}
        else:
            # Most slots are provided by the core snap and specified this way.
            slot = {'slot': item['interface']}

        req = {
            'action': 'connect',
            'slots': [slot],
            'plugs': [{'snap': item['snap'], 'plug': item['plug']}]
        }
        print("snap connect {snap}:{plug} {interface}".format(**item))
        router_request("POST", url, json=req, dump=False)
