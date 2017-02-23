###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

"""
Functions associated with deploying and cleaning up docker containers.
"""

import docker
import json
import os
import platform
import random
import re
import subprocess
import time
import yaml

from paradrop.base.output import out
from paradrop.base import nexus, settings
from paradrop.lib.misc import resopt
from paradrop.lib.utils import pdos, pdosq
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.config.devices import getWirelessPhyName

from .chutecontainer import ChuteContainer
from .dockerfile import Dockerfile
from .downloader import downloader


DOCKER_CONF = """
# Docker systemd configuration
#
# This configuration file was automatically generated by Paradrop.  Any changes
# will be overwritten on startup.

# Tell docker not to start containers automatically on startup.
DOCKER_OPTIONS="--restart=false"
"""

# Used to match and suppress noisy progress messages from Docker output.
#
# Example:
# Extracting
# 862a3e9af0ae
# [================================================>  ] 64.06 MB/65.7 MB
suppress_re = re.compile("^(Downloading|Extracting|[a-z0-9]+|\[=*>?\s*\].*)$")


def getImageName(chute):
    if hasattr(chute, 'external_image'):
        return chute.external_image
    elif hasattr(chute, 'version'):
        return "{}:{}".format(chute.name, chute.version)
    else:
        # Compatibility with old chutes missing version numbers.
        return "{}:latest".format(chute.name)


def getPortList(chute):
    """
    Get a list of ports to expose in the format expected by create_container.

    Uses the port binding dictionary from the chute host_config section.
    The keys are expected to be integers or strings in one of the
    following formats: "port" or "port/protocol".

    Example:
    port_bindings = {
        "1111/udp": 1111,
        "2222": 2222
    }
    getPortList returns [(1111, 'udp'), (2222, 'tcp')]
    """
    if not hasattr(chute, 'host_config') or chute.host_config == None:
        config = {}
    else:
        config = chute.host_config

    ports = []
    for port in config.get('port_bindings', {}).keys():
        if isinstance(port, int):
            ports.append((port, 'tcp'))
            continue

        parts = port.split('/')
        if len(parts) == 1:
            ports.append((int(parts[0]), 'tcp'))
        else:
            ports.append((int(parts[0]), parts[1]))

    # If the chute is configured to host a web service, check
    # whether there is already an entry in the list for the
    # web port.  If not, we should add one.
    web_port = chute.getWebPort()
    if web_port is not None:
        if not any(p[0] == web_port for p in ports):
            ports.append((web_port, 'tcp'))

    return ports


def writeDockerConfig():
    """
    Write options to Docker configuration.

    Mainly, we want to tell Docker not to start containers automatically on
    system boot.
    """
    # First we have to find the configuration file.
    # On ubuntu 16.04 with docker snap, it should be in
    # "/var/snap/docker/{version}/etc/docker/", but version could change.
    path = "/var/snap/docker/current/etc/docker/docker.conf"

    written = False
    if os.path.exists(path):
        try:
            with open(path, "w") as output:
                output.write(DOCKER_CONF)
            written = True
        except Exception as e:
            out.warn('Error writing to {}: {}'.format(path, str(e)))

    if not written:
        out.warn('Could not write docker configuration.')
    return written


def buildImage(update):
    """
    Build the Docker image and monitor progress.
    """
    out.info('Building image for {}\n'.format(update.new))

    client = docker.Client(base_url="unix://var/run/docker.sock", version='auto')

    repo = getImageName(update.new)

    if hasattr(update.new, 'external_image'):
        # If the pull fails, we will fall through and attempt a local build.
        # Be aware, in that case, the image will be tagged as if it came from
        # the registry (e.g. registry.exis.io/image) but will have a different
        # image id from the published version.  The build should be effectively
        # the same, though.
        pulled = _pullImage(update, client)
        if pulled:
            return None
        else:
            update.progress("Pull failed, attempting a local build.")

    if hasattr(update, 'dockerfile'):
        buildSuccess = _buildImage(update, client, True,
                rm=True, tag=repo, fileobj=update.dockerfile)
    elif hasattr(update, 'download'):
        # download field should be an object with at least 'url' but may also
        # contain 'user' and 'secret' for authentication.
        download_args = update.download
        with downloader(**download_args) as dl:
            workDir, meta = dl.fetch()
            buildSuccess = _buildImage(update, client, False,
                    rm=True, tag=repo, path=workDir)
    else:
        raise Exception("No Dockerfile or download location supplied.")

    #If we failed to build skip creating and starting clean up and fail
    if not buildSuccess:
        raise Exception("Building docker image failed; check your Dockerfile for errors.")


def _buildImage(update, client, inline, **buildArgs):
    """
    Build the Docker image and monitor progress (worker function).

    inline: whether Dockerfile is specified as a string or a file in the
    working path.

    Returns True on success, False on failure.
    """
    # Look for additional build information, either as a dictionary in the
    # update object or a YAML file in the checkout directory.
    #
    # If build_conf is specified in both places, we'll let values from
    # the update object override the file.
    build_conf = {}
    if 'path' in buildArgs:
        conf_path = os.path.join(buildArgs['path'], settings.CHUTE_CONFIG_FILE)
        try:
            with open(conf_path, 'r') as source:
                build_conf = yaml.safe_load(source)
        except:
            pass
    if hasattr(update, 'build'):
        build_conf.update(update.build)

    # If this is a light chute, generate a Dockerfile.
    chute_type = build_conf.get('type', 'heavy')
    if chute_type == 'light':
        buildArgs['pull'] = True

        dockerfile = Dockerfile(build_conf)
        valid, reason = dockerfile.isValid()
        if not valid:
            raise Exception("Invalid configuration: {}".format(reason))

        if inline:
            # Pass the dockerfile string directly.
            buildArgs['fileobj'] = dockerfile.getBytesIO()
        else:
            # Write it out to a file in the working directory.
            path = os.path.join(buildArgs['path'], "Dockerfile")
            dockerfile.writeFile(path)

    output = client.build(**buildArgs)

    buildSuccess = True
    for line in output:
        #if we encountered an error make note of it
        if 'errorDetail' in line:
            buildSuccess = False

        for key, value in json.loads(line).iteritems():
            if isinstance(value, dict):
                continue
            else:
                msg = value.rstrip()
                if len(msg) > 0 and suppress_re.match(msg) is None:
                    update.progress(msg)

    return buildSuccess


def _pullImage(update, client):
    """
    Pull the image from a registry.

    Returns True on success, False on failure.
    """
    auth_config = {
        'username': settings.REGISTRY_USERNAME,
        'password': settings.REGISTRY_PASSWORD
    }

    update.progress("Pulling image: {}".format(update.new.external_image))

    layers = 0
    complete = 0

    output = client.pull(update.new.external_image, auth_config=auth_config, stream=True)
    for line in output:
        data = json.loads(line)

        # Suppress lines that have progressDetail set.  Those are the ones with
        # the moving progress bar.
        if data.get('progressDetail', {}) == {}:
            if 'status' not in data or 'id' not in data:
                continue

            update.progress("{}: {}".format(data['status'], data['id']))

            # Count the number of layers that need to be pulled and the number
            # completed.
            status = data['status'].strip().lower()
            if status == 'pulling fs layer':
                layers += 1
            elif status == 'pull complete':
                complete += 1

    update.progress("Finished pulling {} / {} layers".format(complete, layers))
    return (complete > 0 and complete == layers)


def removeNewImage(update):
    """
    Remove the newly built image during abort sequence.
    """
    _removeImage(update.new)


def removeOldImage(update):
    """
    Remove the image for the old version of the chute.
    """
    _removeImage(update.old)


def _removeImage(chute):
    """
    Remove the image for a chute.
    """
    image = getImageName(chute)
    out.info("Removing image {}\n".format(image))

    try:
        client = docker.Client(base_url="unix://var/run/docker.sock",
                version='auto')
        client.remove_image(image=image)
    except Exception as error:
        out.warn("Error removing image: {}".format(error))


def startChute(update):
    """
    Create a docker container based on the passed in update.
    """
    _startChute(update.new)


def startOldContainer(update):
    """
    Create a docker container using the old version of the image.
    """
    _startChute(update.old)


def _startChute(chute):
    """
    Create a docker container based on the passed in chute object.
    """
    out.info('Attempting to start new Chute %s \n' % (chute.name))

    repo = getImageName(chute)
    name = chute.name

    c = docker.Client(base_url="unix://var/run/docker.sock", version='auto')

    host_config = build_host_config(chute, c)

    # Set environment variables for the new container.
    # PARADROP_ROUTER_ID can be used to change application behavior based on
    # what router it is running on.
    environment = prepare_environment(chute)

    # Passing a list of internal port numbers to create_container exposes the
    # ports in case the Dockerfile is missing EXPOSE commands.
    intPorts = getPortList(chute)

    # create_container expects a list of the internal mount points.
    volumes = chute.getCache('volumes')
    intVolumes = [v['bind'] for v in volumes.values()]

    try:
        container = c.create_container(
            image=repo, name=name, host_config=host_config,
            environment=environment, ports=intPorts, volumes=intVolumes
        )
        c.start(container.get('Id'))
        out.info("Successfully started chute with Id: %s\n" % (str(container.get('Id'))))
    except Exception as e:
        raise e

    setup_net_interfaces(chute)


def removeNewContainer(update):
    """
    Remove the newly started container during abort sequence.
    """
    name = update.new.name
    out.info("Removing container {}\n".format(name))

    try:
        client = docker.Client(base_url="unix://var/run/docker.sock",
                version='auto')

        # Grab the last 40 log messages to help with debugging.
        logs = client.logs(name, stream=False, tail=40, timestamps=False)
        update.progress("{}: {}".format(name, logs.rstrip()))

        client.remove_container(container=name, force=True)
    except Exception as error:
        out.warn("Error removing container: {}".format(error))


def removeChute(update):
    """
    Remove a docker container and the image it was built on based on the passed in update.

    :param update: The update object containing information about the chute.
    :type update: obj
    :returns: None
    """
    out.info('Attempting to remove chute %s\n' % (update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock', version='auto')
    repo = getImageName(update.old)
    name = update.name

    try:
        c.remove_container(container=name, force=True)
    except Exception as e:
        update.progress(str(e))

    try:
        c.remove_image(image=repo)
    except Exception as e:
        update.progress(str(e))


def removeOldContainer(update):
    """
    Remove the docker container for the old version of a chute.

    :param update: The update object containing information about the chute.
    :type update: obj
    :returns: None
    """
    out.info('Attempting to remove chute %s\n' % (update.name))
    client = docker.Client(base_url='unix://var/run/docker.sock', version='auto')

    try:
        client.remove_container(container=update.old.name, force=True)
    except Exception as e:
        update.progress(str(e))


def stopChute(update):
    """
    Stop a docker container based on the passed in update.

    :param update: The update object containing information about the chute.
    :type update: obj
    :returns: None
    """
    out.info('Attempting to stop chute %s\n' % (update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock', version='auto')
    c.stop(container=update.name)

def restartChute(update):
    """
    Start a docker container based on the passed in update.

    :param update: The update object containing information about the chute.
    :type update: obj
    :returns: None
    """
    out.info('Attempting to restart chute %s\n' % (update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock', version='auto')
    c.start(container=update.name)

    setup_net_interfaces(update.new)


def getBridgeGateway():
    """
    Look up the gateway IP address for the docker bridge network.

    This is the docker0 IP address; it is the IP address of the host from the
    chute's perspective.
    """
    client = docker.Client(base_url="unix://var/run/docker.sock", version='auto')
    info = client.inspect_network("bridge")
    for config in info['IPAM']['Config']:
        if 'Gateway' in config:
            return config['Gateway']

    # Fall back to a default if we could not find it.  This address will work
    # in most places unless Docker changes to use a different address.
    out.warn('Could not find bridge gateway, using default')
    return '172.17.0.1'


def prepare_port_bindings(chute):
    host_config = chute.getHostConfig()
    bindings = host_config.get('port_bindings', {}).copy()

    # If the chute is configured to host a web service, check
    # whether there is a host port binding associated with it.
    # If not, we will add blank one so that Docker dynamically
    # assigns a port in the host to forward to the container.
    web_port = chute.getWebPort()
    if web_port is not None:
        # The port could appear in multiple formats, e.g. 80, 80/tcp.
        # If any of them are present, we do not need to add anything.
        keys = [web_port, str(web_port), "{}/tcp".format(web_port)]
        if not any(k in bindings for k in keys):
            bindings["{}/tcp".format(web_port)] = None

    return bindings


def build_host_config(chute, client=None):
    """
    Build the host_config dict for a docker container based on the passed in update.

    :param chute: The chute object containing information about the chute.
    :type chute: obj
    :param client: Docker client object.
    :returns: (dict) The host_config dict which docker needs in order to create the container.
    """
    if client is None:
        client = docker.Client(base_url="unix://var/run/docker.sock", version='auto')

    config = chute.getHostConfig()

    extra_hosts = {}
    network_mode = config.get('network_mode', 'bridge')
    volumes = chute.getCache('volumes')

    # We are not able to set extra_hosts if the network_mode is set to 'host'.
    # In that case, the chute uses the same /etc/hosts file as the host system.
    if network_mode != 'host':
        extra_hosts[settings.LOCAL_DOMAIN] = getBridgeGateway()

    # If the chute has not configured a host binding for port 80, let Docker
    # assign a dynamic one.  We will use it to redirect HTTP requests to the
    # chute.
    port_bindings = prepare_port_bindings(chute)

    # restart_policy: set to 'no' to prevent Docker from starting containers
    # automatically on system boot.  Paradrop will set up the host environment
    # first, then restart the containers.
    host_conf = client.create_host_config(
        #TO support
        port_bindings=port_bindings,
        dns=config.get('dns'),
        network_mode=network_mode,
        extra_hosts=extra_hosts,
        binds=volumes,
        #links=config.get('links'),
        #restart_policy={'MaximumRetryCount': 5, 'Name': 'on-failure'},
        restart_policy={'Name': 'no'},
        devices=config.get('devices', []),
        lxc_conf={},
        publish_all_ports=False,
        privileged=config.get('privileged', False),
        dns_search=[],
        volumes_from=None,
        cap_add=['NET_ADMIN'],
        cap_drop=[]
    )
    return host_conf


def call_retry(cmd, env, delay=3, tries=3):
    while tries >= 0:
        tries -= 1

        out.info("Calling: {}\n".format(" ".join(cmd)))
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, env=env)
            for line in proc.stdout:
                out.info("{}: {}\n".format(cmd[0], line.strip()))
            for line in proc.stderr:
                out.warn("{}: {}\n".format(cmd[0], line.strip()))
            return proc.returncode
        except OSError as e:
            out.warn('Command "{}" failed\n'.format(" ".join(cmd)))
            if tries <= 0:
                out.exception(e, True)
                raise e

        time.sleep(delay)


def setup_net_interfaces(chute):
    """
    Link interfaces in the host to the internal interfaces in the Docker
    container.

    The commands are based on the pipework script
    (https://github.com/jpetazzo/pipework).

    :param chute: The chute object containing information about the chute.
    :type update: obj
    :returns: None
    """
    interfaces = chute.getCache('networkInterfaces')

    # Construct environment for subprocess calls.
    env = {
        "PATH": os.environ.get("PATH", "/bin")
    }
    if settings.DOCKER_BIN_DIR not in env['PATH']:
        env['PATH'] += ":" + settings.DOCKER_BIN_DIR

    # We need the chute's PID in order to work with Linux namespaces.
    container = ChuteContainer(chute.name)
    pid = container.getPID()

    for iface in interfaces:
        if iface.get('netType') == 'wifi':
            IP = iface.get('ipaddrWithPrefix')
            internalIntf = iface.get('internalIntf')
            externalIntf = iface.get('externalIntf')
        else: # pragma: no cover
            continue

        mode = iface.get('mode', 'ap')

        if mode == 'ap':
            # Generate a temporary interface name.  It just needs to be unique.
            # We will rename to the internalIntf name as soon as the interface
            # is inside the chute.
            tmpIntf = "tmp{:x}".format(random.getrandbits(32))

            # TODO copy MTU from original interface?
            cmd = ['ip', 'link', 'add', 'link', externalIntf, 'dev', tmpIntf,
                    'type', 'macvlan', 'mode', 'bridge']
            call_retry(cmd, env, tries=1)

            # Bring the interface up.
            cmd = ['ip', 'link', 'set', tmpIntf, 'up']
            call_retry(cmd, env, tries=1)

            # Give the new interface to the chute.
            cmd = ['ip', 'link', 'set', tmpIntf, 'netns', str(pid)]
            call_retry(cmd, env, tries=1)

            # Rename the interface according to what the chute wants.
            cmd = ['ip', 'link', 'set', tmpIntf, 'name', internalIntf]
            call_in_netns(chute, env, cmd)

            # Set the IP address.
            cmd = ['ip', 'addr', 'add', IP, 'dev', internalIntf]
            call_in_netns(chute, env, cmd)

            # Bring the interface up again.
            cmd = ['ip', 'link', 'set', internalIntf, 'up']
            call_in_netns(chute, env, cmd)

        elif mode == 'monitor':
            phyname = getWirelessPhyName(externalIntf)

            cmd = ['iw', 'phy', phyname, 'set', 'netns', str(pid)]
            call_retry(cmd, env, tries=1)

            # Rename the interface inside the container.
            cmd = ['ip', 'link', 'set', 'dev', externalIntf, 'up', 'name',
                    internalIntf]
            call_in_netns(chute, env, cmd)


def call_in_netns(chute, env, command):
    """
    Call command within a chute's namespace.

    command: should be a list of strings.
    """
    # We need the chute's PID in order to work with Linux namespaces.
    container = ChuteContainer(chute.name)
    pid = container.getPID()

    # Set up netns directory and link so that 'ip netns' command works.
    pdosq.makedirs('/var/run/netns')
    netns_link = '/var/run/netns/{}'.format(pid)
    cmd = ['ln', '-s', '/proc/{}/ns/net'.format(pid), netns_link]
    call_retry(cmd, env, tries=1)

    # Try first with `ip netns exec`.  This is preferred because it works using
    # commands in the host.  We cannot be sure the `docker exec` version will
    # work with all chute images.
    cmd = ['ip', 'netns', 'exec', str(pid)] + command
    try:
        code = call_retry(cmd, env, tries=1)
    except:
        code = -1
    finally:
        # Clean up the link.
        pdos.remove(netns_link)

    # We fall back to `docker exec` which relies on the container image having
    # an `ip` command available to configure interfaces from within.
    if code != 0:
        out.warn("ip netns exec command failed, resorting to docker exec\n")

        client = docker.Client(base_url="unix://var/run/docker.sock", version='auto')
        status = client.exec_create(chute.name, command, user='root')
        client.exec_start(status['Id'])


def prepare_environment(chute):
    """
    Prepare environment variables for a chute container.
    """
    # Make a copy so that we do not alter the original, which only contains
    # user-specified environment variables.
    env = getattr(chute, 'environment', {}).copy()

    env['PARADROP_CHUTE_NAME'] = chute.name
    env['PARADROP_ROUTER_ID'] = nexus.core.info.pdid
    env['PARADROP_DATA_DIR'] = chute.getCache('internalDataDir')
    env['PARADROP_SYSTEM_DIR'] = chute.getCache('internalSystemDir')

    if hasattr(chute, 'version'):
        env['PARADROP_CHUTE_VERSION'] = chute.version

    return env


def _setResourceAllocation(allocation):
    client = docker.Client(base_url="unix://var/run/docker.sock", version='auto')
    for chutename, resources in allocation.iteritems():
        out.info("Update chute {} set cpu_shares={}\n".format(
            chutename, resources['cpu_shares']))
        client.update_container(container=chutename,
                cpu_shares=resources['cpu_shares'])

        # Using class id 1:1 for prioritized, 1:3 for best effort.
        # Prioritization is implemented in confd/qos.py.  Class-ID is
        # represented in hexadecimal.
        # Reference: https://www.kernel.org/doc/Documentation/cgroup-v1/net_cls.txt
        if resources.get('prioritize_traffic', False):
            classid = "0x10001"
        else:
            classid = "0x10003"

        container = ChuteContainer(chutename)
        try:
            container_id = container.getID()
            fname = "/sys/fs/cgroup/net_cls/docker/{}/net_cls.classid".format(container_id)
            with open(fname, "w") as output:
                output.write(classid)
        except Exception as error:
            out.warn("Error setting traffic class: {}\n".format(error))


def setResourceAllocation(update):
    allocation = update.new.getCache('newResourceAllocation')
    _setResourceAllocation(allocation)


def revertResourceAllocation(update):
    allocation = update.new.getCache('oldResourceAllocation')
    _setResourceAllocation(allocation)


def removeAllContainers(update):
    """
    Remove all containers on the system.  This should only be used as part of a
    factory reset mechanism.

    :returns: None
    """
    client = docker.Client(base_url='unix://var/run/docker.sock', version='auto')

    for container in client.containers(all=True):
        try:
            client.remove_container(container=container['Id'], force=True)
        except Exception as e:
            update.progress(str(e))
