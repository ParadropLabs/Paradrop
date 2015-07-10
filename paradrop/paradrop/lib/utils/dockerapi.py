###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.lib.utils.output import out, logPrefix
import docker
import json


def startChute(update):
    print update.__dict__
    out.warn('** %s TODO implement me\n' % logPrefix())

    repo = update.name + ":latest"
    dockerfile = update.dockerfile
    name = update.name

    host_config = {}#build_host_config(update)
    
    c = docker.Client(base_url="unix://var/run/docker.sock")

    for line in c.build(rm=True, tag=repo, fileobj=dockerfile):
        for key, value in json.loads(line).iteritems():
            if (isinstance(value, dict)):
                continue
            elif(key == 'stream'):
                update.pkg.request.write(str(value))
            else:
                update.pkg.request.write(str(value) + '\n')
    container = c.create_container(
        image=repo, name=name, host_config=host_config
    )

    out.info("-- %s %s\n" % (logPrefix(), str(container.get('Id'))))
    c.start(container.get('Id'))


def stopChute(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    c = docker.Client(base_url='unix://var/run/docker.sock')
    repo = update.name + ":latest"
    name = update.name
    c.stop(container=name)
    c.remove_container(container=name)
    c.remove_image(image=repo)

def build_host_config(update):

    return docker.utils.create_host_config(
        #TO support
        port_bindings=port_bindings,
        restart_policy={"MaximumRetryCount": 0, "Name": "always"},
        network_mode='bridge',
        binds=binds,
        links={},
        extra_hosts={},
        dns=[],
        #not supported
        devices=[],
        lxc_conf={},
        publish_all_ports=False,
        privileged=False,
        dns_search=[],
        volumes_from=None,
        cap_add=[],
        cap_drop=[]
    )

