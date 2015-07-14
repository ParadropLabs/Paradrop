###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.lib.utils.output import out, logPrefix
import docker
import json


def startChute(update):
    out.info('-- %s Attempting to start new Chute %s \n' % (logPrefix(), update.name))

    repo = update.name + ":latest"
    dockerfile = update.dockerfile
    name = update.name

    host_config = build_host_config(update)
    
    c = docker.Client(base_url="unix://var/run/docker.sock")

    for line in c.build(rm=True, tag=repo, fileobj=dockerfile):
        for key, value in json.loads(line).iteritems():
            if isinstance(value, dict):
                continue
            elif key == 'stream':
                update.pkg.request.write(str(value))
            else:
                update.pkg.request.write(str(value) + '\n')
    container = c.create_container(
        image=repo, name=name, host_config=host_config
    )

    out.info("-- %s Successfully started chute with Id: %s\n" % (logPrefix(), str(container.get('Id'))))
    c.start(container.get('Id'))

def removeChute(update):
    out.info('-- %s Attempting to remove chute %s\n' % (logPrefix(), update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock')
    repo = update.name + ":latest"
    name = update.name
    try:
        c.remove_container(container=name, force=True)
        c.remove_image(image=repo)
    except Exception as e:
        update.complete(success=False, message= e.explanation)

def stopChute(update):
    out.info('-- %s Attempting to stop chute %s\n' % (logPrefix(), update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock')
    try:
        c.stop(container=update.name)
    except Exception as e:
        update.complete(success=False, message= e.explanation)

def restartChute(update):
    out.info('-- %s Attempting to start chute %s\n' % (logPrefix(), update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock')
    try:
        c.start(container=update.name)
    except Exception as e:
        update.complete(success=False, message= e.explanation)

def build_host_config(update):

    return docker.utils.create_host_config(
        #TO support
        port_bindings=update.host_config.get('port_bindings'),
        restart_policy=update.host_config.get('restart_policy'),
        binds=update.host_config.get('binds'),
        links=update.host_config.get('links'),
        dns=update.host_config.get('dns'),
        #not supported
        #network_mode=update.host_config.get('network_mode'),
        #extra_hosts=update.host_config.get('extra_hosts'),
        devices=[],
        lxc_conf={},
        publish_all_ports=False,
        privileged=False,
        dns_search=[],
        volumes_from=None,
        cap_add=[],
        cap_drop=[]
    )

