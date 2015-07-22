###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from pdtools.lib.output import out
import docker
import json
import subprocess


def startChute(update):
    out.info('Attempting to start new Chute %s \n' % (update.name))

    repo = update.name + ":latest"
    dockerfile = update.dockerfile
    name = update.name

    host_config = build_host_config(update)
    
    c = docker.Client(base_url="unix://var/run/docker.sock", version='auto')

    #Get Id's of current images for comparison upon failure
    validImages = c.images(quiet=True, all=False)

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
        #Clean up docker container from failed build
        rmv = c.containers(latest=True)
        for cntr in rmv:
            c.remove_container(container=cntr.get('Id'), force=True)

        #Clean up image from failed build
        currImages = c.images(quiet=True, all=False)
        for img in currImages:
            if not img in validImages:
                out.info('-- %s Removing Invalid image with id: %s' % (logPrefix(), str(img)))
                c.remove_image(image=img)

        #Notify user and throw exception
        update.complete(success=False, message ="Build process failed check your Dockerfile for errors.")
        raise Exception('Building of docker image failed.')
        return

    container = c.create_container(
        image=repo, name=name, host_config=host_config
    )

    c.start(container.get('Id'))
    out.info("Successfully started chute with Id: %s\n" % (str(container.get('Id'))))
    setup_net_interfaces(update)

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

def restartChute(update):
    out.info('Attempting to start chute %s\n' % (update.name))
    c = docker.Client(base_url='unix://var/run/docker.sock', version='auto')
    try:
        c.start(container=update.name)
    except Exception as e:
        update.complete(success=False, message= e.explanation)

def build_host_config(update):

    return docker.utils.create_host_config(
        #TO support
        port_bindings=update.host_config.get('port_bindings'),
        binds=update.host_config.get('binds'),
        links=update.host_config.get('links'),
        dns=update.host_config.get('dns'),
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
        cap_add=[],
        cap_drop=[]
    )

def setup_net_interfaces(update):
    interfaces = update.new.getCache('networkInterfaces')
    for iface in interfaces:
        if iface.get('netType') == 'wifi':
            IP = iface.get('ipaddrWithPrefix')
            internalIntf = iface.get('internalIntf')
            externalIntf = iface.get('externalIntf')
        else:
            continue

        cmd = ['/apps/paradrop/current/bin/pipework', externalIntf, '-i', internalIntf, update.name,  IP]
        try:
            result = subprocess.call(cmd)
        except OSError as e:
            out.warn('Command "{}" failed\n'.format(" ".join(cmd)))
            out.exception(e, True)
            raise e
