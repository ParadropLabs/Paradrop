###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from pdtools.lib.output import out
import docker
import json
import os
import subprocess

from paradrop.lib import settings


def startChute(update):
    out.info('Attempting to start new Chute %s \n' % (update.name))

    repo = update.name + ":latest"
    dockerfile = update.dockerfile
    name = update.name

    host_config = build_host_config(update)

    c = docker.Client(base_url="unix://var/run/docker.sock", version='auto')

    #Get Id's of current images for comparison upon failure
    validImages = c.images(quiet=True, all=False)
    validContainers = c.containers(quiet=True, all=True)

    buildFailed = False
    for line in c.build(rm=True, tag=repo, fileobj=dockerfile):

        #if we encountered an error make note of it
        if 'errorDetail' in line:
            buildFailed = True

        for key, value in json.loads(line).iteritems():
            if isinstance(value, dict):
                continue
            elif key == 'stream':
                update.pkg.request.write(str(value))
            else:
                update.pkg.request.write(str(value) + '\n')

    #If we failed to build skip creating and starting clean up and fail
    if buildFailed:
        failAndCleanUpDocker(validImages, validContainers, update)

    try:
        container = c.create_container(
            image=repo, name=name, host_config=host_config
        )
        c.start(container.get('Id'))
    except Exception as e:
        failAndCleanUpDocker(validImages, validContainers, update)
    
    out.info("Successfully started chute with Id: %s\n" % (str(container.get('Id'))))

    setup_net_interfaces(update)

def failAndCleanUpDocker(validImages, validContainers, update):
    c = docker.Client(base_url="unix://var/run/docker.sock", version='auto')

    #Clean up containers from failed build/start
    currContainers = c.containers(quiet=True, all=True)
    for cntr in currContainers:
        if not cntr in validContainers:
            out.info('Removing Invalid container with id: %s' % str(cntr.get('Id')))
            c.remove_container(container=cntr.get('Id'))

    #Clean up images from failed build
    currImages = c.images(quiet=True, all=False)
    for img in currImages:
        if not img in validImages:
            out.info('Removing Invalid image with id: %s' % str(img))
            c.remove_image(image=img)
    #Notify user and throw exception
    update.complete(success=False, message ="Build or starting your container failed check your Dockerfile for errors.")
    raise Exception('Building or starting of docker image failed.')


def removeChute(update):
    out.info('Attempting to remove chute %s\n' % (update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock', version='auto')
    repo = update.name + ":latest"
    name = update.name
    try:
        c.remove_container(container=name, force=True)
        c.remove_image(image=repo)
    except Exception as e:
        update.complete(success=False, message= e.explanation)

def stopChute(update):
    out.info('Attempting to stop chute %s\n' % (update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock', version='auto')
    try:
        c.stop(container=update.name)
    except Exception as e:
        update.complete(success=False, message= e.explanation)
        raise e

def restartChute(update):
    out.info('Attempting to restart chute %s\n' % (update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock', version='auto')
    try:
        c.start(container=update.name)
    except Exception as e:
        update.complete(success=False, message= e.explanation)
        raise e

    setup_net_interfaces(update)

def build_host_config(update):

    if not hasattr(update.new, 'host_config') or update.new.host_config == None:
        config = dict()
    else:
        config = update.new.host_config

    host_conf = docker.utils.create_host_config(
        #TO support
        port_bindings=config.get('port_bindings'),
        binds=config.get('binds'),
        links=config.get('links'),
        dns=config.get('dns'),
        #not supported/managed by us
        #network_mode=update.host_config.get('network_mode'),
        #extra_hosts=update.host_config.get('extra_hosts'),
        restart_policy={'MaximumRetryCount': 5, 'Name': 'always'},
        devices=[],
        lxc_conf={},
        publish_all_ports=False,
        privileged=False,
        dns_search=[],
        volumes_from=None,
        cap_add=['NET_ADMIN'],
        cap_drop=[]
    )
    return host_conf


def setup_net_interfaces(update):
    interfaces = update.new.getCache('networkInterfaces')
    for iface in interfaces:
        if iface.get('netType') == 'wifi':
            IP = iface.get('ipaddrWithPrefix')
            internalIntf = iface.get('internalIntf')
            externalIntf = iface.get('externalIntf')
        else:
            continue

        # Construct environment for pipework call.  It only seems to require
        # the PATH variable to include the directory containing the docker
        # client.  On Snappy this was not happening by default, which is why
        # this code is here.
        env = {"PATH": os.environ.get("PATH", "")}
        if settings.DOCKER_BIN_DIR not in env['PATH']:
            env['PATH'] += ":" + settings.DOCKER_BIN_DIR

        cmd = ['/apps/paradrop/current/bin/pipework', externalIntf, '-i',
               internalIntf, update.name,  IP]
        out.info("Calling: {}\n".format(" ".join(cmd)))
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, env=env)
            for line in proc.stdout:
                out.info("pipework: {}\n".format(line.strip()))
            for line in proc.stderr:
                out.warn("pipework: {}\n".format(line.strip()))
        except OSError as e:
            out.warn('Command "{}" failed\n'.format(" ".join(cmd)))
            out.exception(e, True)
            raise e
